# pyright: reportMissingImports=false
"""Game session state: registration, game_id, players. Used by handlers and Web API."""
import uuid
from typing import Any

# In-memory store for active games (by game_id) so Web App can resolve state.
# Format: { game_id: { "chat_id": int, "players": { user_id: name }, "game_active": bool } }
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
    return bool(get_players(chat_data)) and not is_game_active(chat_data)


def finish_registration(chat_id: int, chat_data: dict[str, Any]) -> str:
    """
    Lock registration, set game_active, create game_id, store in global map for Web API.
    Returns game_id.
    """
    game_id = str(uuid.uuid4())
    chat_data["game_active"] = True
    chat_data["game_id"] = game_id
    _games_by_id[game_id] = {
        "chat_id": chat_id,
        "players": dict(chat_data.get("players") or {}),
        "game_active": True,
    }
    return game_id


def get_game_by_id(game_id: str) -> dict[str, Any] | None:
    """For Web API: get game state by game_id."""
    return _games_by_id.get(game_id)


def end_game_chat(chat_data: dict[str, Any]) -> None:
    """Clear game state for this chat (e.g. on /end_game)."""
    game_id = chat_data.pop("game_id", None)
    if game_id:
        _games_by_id.pop(game_id, None)
    chat_data["game_active"] = False
    chat_data["players"] = {}
    chat_data.pop("registration_msg_id", None)


def end_game_by_id(game_id: str) -> None:
    """Remove game from global store (e.g. when game ends from Web)."""
    _games_by_id.pop(game_id, None)
