# pyright: reportMissingImports=false
"""Game auth for Web API and WebSocket.

HTTP: resolve game and player from request headers (initData, late join).
WS: validate initData and require existing player in game["players"].
Raises HTTPException on failure."""
import logging
from typing import Any

from fastapi import HTTPException, Request

from config.config import config
from services.game_session import get_game_by_id, save_game
from utils.telegram_webapp import (
    get_user_first_name_from_validated,
    get_user_id_from_validated,
    validate_init_data,
)

logger = logging.getLogger(__name__)

GAME_NOT_FOUND_DETAIL = "משחק לא נמצא או שהסתיים."
INIT_DATA_REQUIRED_DETAIL = "פתחו את המשחק בלחיצה על הכפתור שמופיע בהודעה בקבוצה (כניסה למשחק או שחק עכשיו)."
WS_PLAYERS_ONLY_DETAIL = "רק שחקנים רשומים יכולים לקבל עדכונים בזמן אמת."


def _validate_and_load_game(game_id: str, init_data: str) -> tuple[dict, int | None, Any]:
    """Load game; if init_data present, validate and return (game, user_id, validated). Otherwise (game, None, None). Raises HTTPException on 401/404."""
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=GAME_NOT_FOUND_DETAIL)
    init_data = (init_data or "").strip()
    if not init_data:
        return (game, None, None)
    token = config.TELEGRAM_TOKEN or ""
    validated = validate_init_data(init_data, token)
    if not validated:
        raise HTTPException(status_code=401, detail=INIT_DATA_REQUIRED_DETAIL)
    user_id = get_user_id_from_validated(validated)
    if user_id is None:
        raise HTTPException(status_code=401, detail=INIT_DATA_REQUIRED_DETAIL)
    return (game, user_id, validated)


def get_game_for_request(game_id: str, request: Request) -> dict:
    """Load game; validate Telegram initData when present; perform late join if needed. Raises HTTPException on 401/404."""
    init_data = request.headers.get("X-Telegram-Init-Data") or ""
    game, user_id, validated = _validate_and_load_game(game_id, init_data)
    if user_id is None:
        return game
    players = game.get("players") or {}
    if str(user_id) not in players:
        name = get_user_first_name_from_validated(validated)
        players[str(user_id)] = name
        game["players"] = players
        save_game(game_id, game)
        logger.info("Late join: added user_id=%s to game_id=%s as %s", user_id, game_id, name)
    return game


def get_game_and_user_for_ws(game_id: str, init_data: str) -> tuple[dict, int]:
    """Resolve game and user_id for WebSocket connection.

    Requires valid initData and that the user is already in game["players"].
    Raises HTTPException with status_code 401/403/404 on failure.
    """
    if not (init_data or "").strip():
        raise HTTPException(status_code=401, detail=INIT_DATA_REQUIRED_DETAIL)
    game, user_id, _ = _validate_and_load_game(game_id, init_data)
    assert user_id is not None  # _validate_and_load_game raises if init_data present and invalid
    players = game.get("players") or {}
    if str(user_id) not in players:
        raise HTTPException(status_code=403, detail=WS_PLAYERS_ONLY_DETAIL)
    return game, int(user_id)
