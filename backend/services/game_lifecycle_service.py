# pyright: reportMissingImports=false
"""Game lifecycle: start, time up, door opened. Pure business logic; raises HTTPException where appropriate."""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from services.game_api_service import all_unlock_puzzles_solved
from services.game_session import end_game_by_id, save_game
from services.group_repository import set_finished_at
from services.ws_registry import broadcast_door_opened, broadcast_game_over

logger = logging.getLogger(__name__)

TIME_UP_MESSAGE = "⏰ הזמן נגמר! Game Over.\n\nהמשחק הסתיים. כתבו /start_game כדי להתחיל מחדש."
DOOR_NOT_READY_DETAIL = "עדיין לא פתרתם את כל החידות בחדר."


def record_game_start(game_id: str, game: dict[str, Any]) -> None:
    """Set started_at if not set and persist. Idempotent."""
    if not game.get("started_at"):
        game["started_at"] = datetime.now(timezone.utc).isoformat()
        save_game(game_id, game)


async def handle_time_up(game_id: str, game: dict[str, Any], bot: Any) -> None:
    """End game: set group finished_at, end session, broadcast game_over, notify Telegram group."""
    chat_id = game.get("chat_id")
    if chat_id is not None:
        set_finished_at(int(chat_id))
    end_game_by_id(game_id)
    await broadcast_game_over(game_id)
    if chat_id is not None and bot is not None:
        try:
            await bot.send_message(
                chat_id=int(chat_id),
                text=TIME_UP_MESSAGE,
            )
        except Exception as e:
            logger.warning(
                "Failed to send time-up message to group chat_id=%s: %s",
                chat_id,
                e,
            )


async def handle_door_opened(game_id: str, game: dict[str, Any]) -> None:
    """Ensure all unlock puzzles are solved, then broadcast door_opened. Raises HTTPException(400) if not ready."""
    if not all_unlock_puzzles_solved(game):
        raise HTTPException(status_code=400, detail=DOOR_NOT_READY_DETAIL)
    await broadcast_door_opened(game_id)
