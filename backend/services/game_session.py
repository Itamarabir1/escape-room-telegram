# pyright: reportMissingImports=false
"""Game session state: registration, game_id, players. Used by handlers and Web API.
When REDIS_URL is set, game state is stored in Redis; otherwise in-memory."""
import logging
import uuid
from typing import Any

from infrastructure.redis.redis_client import (
    redis_delete_game,
    redis_get_game,
    redis_set_game,
)

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is not available.
# Format: { game_id: { "chat_id": int, "players": { user_id: name }, "game_active": bool, ... } }
_games_by_id: dict[str, dict[str, Any]] = {}


def start_registration(chat_data: dict[str, Any]) -> None:
    """Start a new registration round. Clears players and sets game_active False."""
    chat_data["players"] = {}
    chat_data["game_active"] = False
    chat_data.pop("game_id", None)
    chat_data.pop("registration_msg_id", None)


def add_player(chat_data: dict[str, Any], user_id: int, name: str) -> bool:
    """Add player to registration. Returns True if added, False if already registered."""
    if "players" not in chat_data:
        chat_data["players"] = {}
    if user_id in chat_data["players"]:
        return False
    chat_data["players"][user_id] = name
    return True


def is_game_active(chat_data: dict[str, Any]) -> bool:
    return bool(chat_data.get("game_active"))


def get_players(chat_data: dict[str, Any]) -> dict[int, str]:
    return chat_data.get("players") or {}


def get_players_list_text(chat_data: dict[str, Any]) -> str:
    players = get_players(chat_data)
    return "\n".join([f"- {name}" for name in players.values()]) if players else ""


def can_start_game(chat_data: dict[str, Any]) -> bool:
    """True if registration is open (game not started yet). Allows solo play (0 players)."""
    return not is_game_active(chat_data)


def finish_registration(chat_id: int, chat_data: dict[str, Any]) -> str:
    """
    Lock registration, set game_active, create game_id, store in Redis (or in-memory).
    Returns game_id.
    """
    game_id = str(uuid.uuid4())
    chat_data["game_active"] = True
    chat_data["game_id"] = game_id
    game = {
        "chat_id": chat_id,
        "players": dict(chat_data.get("players") or {}),
        "game_active": True,
    }
    _games_by_id[game_id] = game
    redis_set_game(game_id, game)
    logger.info("Game created: game_id=%s chat_id=%s", game_id, chat_id)
    return game_id


def get_game_by_id(game_id: str) -> dict[str, Any] | None:
    """For Web API: get game state by game_id (Redis first, then in-memory)."""
    found = redis_get_game(game_id)
    if found is not None:
        _games_by_id[game_id] = found  # keep in-memory in sync for handlers
        return found
    found = _games_by_id.get(game_id)
    logger.debug("get_game_by_id game_id=%s found=%s", game_id, found is not None)
    return found


def save_game(game_id: str, game: dict[str, Any]) -> None:
    """Persist game state to Redis and in-memory (call after mutating game)."""
    _games_by_id[game_id] = game
    redis_set_game(game_id, game)


def end_game_chat(chat_data: dict[str, Any]) -> None:
    """Clear game state for this chat (e.g. on /end_game)."""
    game_id = chat_data.pop("game_id", None)
    if game_id:
        _games_by_id.pop(game_id, None)
        redis_delete_game(game_id)
    chat_data["game_active"] = False
    chat_data["players"] = {}
    chat_data.pop("registration_msg_id", None)
    chat_data.pop("started_by_user_id", None)


def end_game_by_id(game_id: str) -> None:
    """Remove game from store (Redis + in-memory)."""
    _games_by_id.pop(game_id, None)
    redis_delete_game(game_id)
