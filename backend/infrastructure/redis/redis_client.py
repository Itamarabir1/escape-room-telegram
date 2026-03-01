# pyright: reportMissingImports=false
"""Redis-backed game session store. Used when REDIS_URL is set."""
import json
import logging
from typing import Any

import redis

from config.config import config

logger = logging.getLogger(__name__)

_KEY_PREFIX = "game:"
_redis_client: Any = None


def _get_redis():
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
    global _redis_client
    _redis_client = None


def _key(game_id: str) -> str:
    return f"{_KEY_PREFIX}{game_id}"


def redis_get_game(game_id: str) -> dict[str, Any] | None:
    r = _get_redis()
    if not r:
        return None
    try:
        raw = r.get(_key(game_id))
        if not raw:
            return None
        data = json.loads(raw)
        if "players" in data and isinstance(data["players"], dict):
            data["players"] = {str(k): v for k, v in data["players"].items()}
        return data
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        logger.warning("Redis connection lost (get_game): %s", e)
        _clear_redis_on_error()
        return None
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("redis_get_game decode error game_id=%s: %s", game_id, e)
        return None


def redis_set_game(game_id: str, game: dict[str, Any], ttl_seconds: int | None = None) -> bool:
    r = _get_redis()
    if not r:
        return False
    ttl = ttl_seconds if ttl_seconds is not None else getattr(config, "GAME_SESSION_TTL", 86400)
    try:
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
    return _get_redis() is not None


# Leaderboard: sorted set "leaderboard", score = seconds to complete (lower = better).
# Writing to this key (e.g. on game end) can be added later.
_LEADERBOARD_KEY = "leaderboard"


def redis_get_leaderboard_top10() -> list[tuple[str, float]]:
    """Return top 10 from Redis sorted set 'leaderboard' (ascending = best first). Returns [(member, score), ...] or []."""
    r = _get_redis()
    if not r:
        return []
    try:
        raw = r.zrange(_LEADERBOARD_KEY, 0, 9, withscores=True)
        if not raw:
            return []
        result: list[tuple[str, float]] = []
        for item in raw:
            member = item[0] if isinstance(item[0], str) else str(item[0])
            score = float(item[1])
            result.append((member, score))
        return result
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        logger.warning("Redis connection lost (get_leaderboard): %s", e)
        _clear_redis_on_error()
        return []
    except (TypeError, ValueError) as e:
        logger.warning("redis_get_leaderboard_top10 error: %s", e)
        return []
