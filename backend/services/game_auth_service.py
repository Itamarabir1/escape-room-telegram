# pyright: reportMissingImports=false
"""Game auth for Web API: resolve game and player from request (initData, late join). Raises HTTPException on failure."""
import logging

from fastapi import HTTPException, Request

from config import config
from services.game_session import get_game_by_id, save_game
from utils.telegram_webapp import (
    get_user_first_name_from_validated,
    get_user_id_from_validated,
    validate_init_data,
)

logger = logging.getLogger(__name__)

GAME_NOT_FOUND_DETAIL = "משחק לא נמצא או שהסתיים."
INIT_DATA_REQUIRED_DETAIL = "פתחו את המשחק בלחיצה על הכפתור שמופיע בהודעה בקבוצה (כניסה למשחק או שחק עכשיו)."


def get_game_for_request(game_id: str, request: Request) -> dict:
    """Load game; validate Telegram initData when present; perform late join if needed. Raises HTTPException on 401/404."""
    init_data = request.headers.get("X-Telegram-Init-Data") or ""
    if not init_data.strip():
        game = get_game_by_id(game_id)
        if not game:
            raise HTTPException(status_code=404, detail=GAME_NOT_FOUND_DETAIL)
        return game
    token = config.TELEGRAM_TOKEN or ""
    validated = validate_init_data(init_data, token)
    if not validated:
        raise HTTPException(status_code=401, detail=INIT_DATA_REQUIRED_DETAIL)
    user_id = get_user_id_from_validated(validated)
    if user_id is None:
        raise HTTPException(status_code=401, detail=INIT_DATA_REQUIRED_DETAIL)
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=GAME_NOT_FOUND_DETAIL)
    players = game.get("players") or {}
    if str(user_id) not in players:
        name = get_user_first_name_from_validated(validated)
        players[str(user_id)] = name
        game["players"] = players
        save_game(game_id, game)
        logger.info("Late join: added user_id=%s to game_id=%s as %s", user_id, game_id, name)
    return game
