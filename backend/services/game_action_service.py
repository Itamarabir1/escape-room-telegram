# pyright: reportMissingImports=false
"""Submit puzzle answer: validate, compare, update state, broadcast. Returns result dict; raises HTTPException on bad request."""
import logging
from typing import Any

from fastapi import HTTPException

from domain.puzzle_status import PuzzleStatus
from data.puzzle_dependencies import get_dependencies_for_item, get_block_message
from services.game_api_service import item_label
from services.game_session import save_game
from services.sse_registry import broadcast_puzzle_solved
from utils.puzzle import (
    ITEM_SUCCESS_MESSAGES,
    SUCCESS_MESSAGE,
    WRONG_MESSAGE,
    normalize_answer,
)

logger = logging.getLogger(__name__)

ITEM_NOT_FOUND_DETAIL = "פריט או חידה לא נמצאו."
NO_ANSWER_REQUIRED_DETAIL = "משימה זו אינה דורשת שליחת תשובה."


async def submit_puzzle_action(
    game_id: str,
    game: dict[str, Any],
    item_id: str,
    answer: str,
    solver_name: str | None,
) -> dict[str, Any]:
    """
    Validate puzzle, compare answer, update room_solved and save if correct, broadcast.
    Returns {"correct": bool, "message": str}. Raises HTTPException(400) when item_id invalid or puzzle is examine-only.
    """
    puzzles = game.get("room_puzzles") or {}
    item_id = (item_id or "").strip()
    if not item_id or item_id not in puzzles:
        raise HTTPException(status_code=400, detail=ITEM_NOT_FOUND_DETAIL)
    p = puzzles[item_id]
    if (p.get("type") or "").lower() == "examine" or not p.get("correct_answer"):
        raise HTTPException(status_code=400, detail=NO_ANSWER_REQUIRED_DETAIL)
    correct_answer = (p.get("correct_answer") or "").strip()
    aliases = p.get("correct_answer_aliases") or []
    accepted = [correct_answer] + [
        str(a).strip() for a in aliases if a is not None and str(a).strip()
    ]
    normalized_user = normalize_answer(answer or "")
    is_correct = any(normalize_answer(a) == normalized_user for a in accepted)
    message = (
        ITEM_SUCCESS_MESSAGES.get(item_id) or SUCCESS_MESSAGE
    ) if is_correct else WRONG_MESSAGE
    if is_correct:
        # Enforce puzzle order: e.g. board_servers only after clock_1
        room_solved = game.get("room_solved") or {}
        required = get_dependencies_for_item(item_id)
        for dep_id in required:
            if room_solved.get(dep_id) != PuzzleStatus.SOLVED.value:
                raise HTTPException(
                    status_code=400,
                    detail=get_block_message(item_id),
                )
        room_solved[item_id] = PuzzleStatus.SOLVED.value
        game["room_solved"] = room_solved
        save_game(game_id, game)
        label = item_label(game, item_id)
        logger.info("WS broadcasting puzzle_solved game_id=%s item_id=%s", game_id, item_id)
        await broadcast_puzzle_solved(
            game_id,
            item_id=item_id,
            item_label=label,
            answer=correct_answer,
            solver_name=solver_name,
        )
    return {"correct": is_correct, "message": message}
