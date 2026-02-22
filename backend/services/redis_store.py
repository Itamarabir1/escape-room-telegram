# pyright: reportMissingImports=false
"""Redis-backed game session store. Used when REDIS_URL is set."""
import json
import logging
from typing import Any

import redis
from config import config

logger = logging.getLogger(__name__)

_KEY_PREFIX = "game:"
_redis_client: Any = None


def _get_redis():
    """Lazy Redis connection. Returns None if REDIS_URL not set or connection fails."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not getattr(config, "REDIS_URL", None):
        return None
    try:
        client = redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
        )
        client.ping()
        _redis_client = client
        logger.info("Redis game store connected: %s", config.REDIS_URL.split("@")[-1] if "@" in config.REDIS_URL else "local")
        return _redis_client
    except Exception as e:
        _redis_client = None
        logger.warning("Redis not available, using in-memory store: %s", e)
        return None


def _clear_redis_on_error():
    """Drop cached client so next request can retry connecting."""
    global _redis_client
    _redis_client = None


def _key(game_id: str) -> str:
    return f"{_KEY_PREFIX}{game_id}"


def redis_get_game(game_id: str) -> dict[str, Any] | None:
    """Load game state from Redis. Returns None if not found or Redis unavailable."""
    r = _get_redis()
    if not r:
        return None
    try:
        raw = r.get(_key(game_id))
        if not raw:
            return None
        data = json.loads(raw)
        # players may be stored as { "123": "name" } (string keys)
        if "players" in data and isinstance(data["players"], dict):
            data["players"] = {int(k): v for k, v in data["players"].items() if str(k).isdigit()}
        return data
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        logger.warning("Redis connection lost (get_game): %s", e)
        _clear_redis_on_error()
        return None
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("redis_get_game decode error game_id=%s: %s", game_id, e)
        return None


def redis_set_game(game_id: str, game: dict[str, Any], ttl_seconds: int | None = None) -> bool:
    """Save game state to Redis. Returns True on success."""
    r = _get_redis()
    if not r:
        return False
    ttl = ttl_seconds if ttl_seconds is not None else getattr(config, "GAME_SESSION_TTL", 86400)
    try:
        # Serialize; players keys as strings for JSON
        out = dict(game)
        if "players" in out and isinstance(out["players"], dict):
            out["players"] = {str(k): v for k, v in out["players"].items()}
        r.setex(_key(game_id), ttl, json.dumps(out, ensure_ascii=False))
        return True
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        logger.warning("Redis connection lost (set_game): %s", e)
        _clear_redis_on_error()
        return False
    except (TypeError, ValueError) as e:
        logger.warning("redis_set_game error game_id=%s: %s", game_id, e)
        return False


def redis_delete_game(game_id: str) -> bool:
    """Remove game from Redis. Returns True if key was deleted or Redis unavailable."""
    r = _get_redis()
    if not r:
        return True
    try:
        r.delete(_key(game_id))
        return True
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        logger.warning("Redis connection lost (delete_game): %s", e)
        _clear_redis_on_error()
        return True
    except Exception as e:
        logger.warning("redis_delete_game error game_id=%s: %s", game_id, e)
        return False


def redis_available() -> bool:
    """True if Redis is configured and reachable."""
    return _get_redis() is not None
