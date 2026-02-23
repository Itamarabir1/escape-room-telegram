# pyright: reportMissingImports=false
"""Game API: state and actions for the Web App.
Frontend client (single place for all API calls): frontend/src/api/client.ts
Schema: domain.game.GameStateResponse

Architecture: Task content and correct answers live in backend (Redis game state).
Room image is not generated at runtime; use demo room (items + positions) or a static image later.
"""
import logging
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import Response

from AI.audio_service import generate_voice_over
from config import config
from data.demo_room import (
    DEMO_ROOM_ITEMS,
    DEMO_ROOM_META,
    DEMO_ROOM_PUZZLES,
)
from domain.game import GameStateResponse, PuzzleResponse
from services.game_session import get_game_by_id, save_game
from utils.puzzle import (
    SAFE_BACKSTORY,
    PROMPT_TEXT,
    SUCCESS_MESSAGE,
    WRONG_MESSAGE,
    normalize_answer,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])

GAME_NOT_FOUND_DETAIL = "משחק לא נמצא או שהסתיים."


def _apply_demo_room(game: dict) -> None:
    """Inject demo room items and puzzles (no image). State is saved to Redis."""
    game["room_name"] = DEMO_ROOM_META["room_name"]
    game["room_description"] = DEMO_ROOM_META["room_description"]
    game["room_lore"] = DEMO_ROOM_META.get("room_lore", "")
    game["room_items"] = [dict(it) for it in DEMO_ROOM_ITEMS]
    game["room_puzzles"] = {}
    for item_id, p in DEMO_ROOM_PUZZLES.items():
        game["room_puzzles"][item_id] = dict(p)


@router.get("/{game_id}")
async def get_game_state(game_id: str) -> GameStateResponse:
    """Returns game state for Web App. When no room exists, applies fixed room (items + positions, no image). Image can be added later as static asset."""
    game = get_game_by_id(game_id)
    if not game:
        logger.warning("get_game_state 404 game_id=%s", game_id)
        raise HTTPException(status_code=404, detail=GAME_NOT_FOUND_DETAIL)

    if not game.get("room_image_url"):
        _apply_demo_room(game)
        save_game(game_id, game)
        logger.info("Room applied for game_id=%s (items + positions, no image)", game_id)

    players_raw = game.get("players", {})
    players_str: dict[str, str] = {str(k): v for k, v in players_raw.items()}
    out: GameStateResponse = {
        "game_id": game_id,
        "players": players_str,
        "game_active": game.get("game_active", True),
    }
    if game.get("room_image_url") or game.get("room_items"):
        if game.get("room_image_url"):
            out["room_image_url"] = game["room_image_url"]
        out["room_name"] = game.get("room_name", "")
        out["room_description"] = game.get("room_description", "")
        out["room_lore"] = game.get("room_lore", "")
        items_raw = game.get("room_items") or []
        out["room_items"] = [
            {"id": it["id"], "label": it["label"], "x": it["x"], "y": it["y"], "action_type": it.get("action_type", "examine")}
            for it in items_raw
        ]
        puzzles_raw = game.get("room_puzzles") or {}
        puzzles_list: list[PuzzleResponse] = []
        first_unlock: PuzzleResponse | None = None
        for item_id, p in puzzles_raw.items():
            ptype = p.get("type") or ("unlock" if p.get("correct_answer") else "examine")
            pr = PuzzleResponse(
                item_id=item_id,
                type=ptype,
                backstory=p.get("backstory", SAFE_BACKSTORY),
            )
            if p.get("encoded_clue"):
                pr["encoded_clue"] = p["encoded_clue"]
            if p.get("prompt_text"):
                pr["prompt_text"] = p["prompt_text"]
            puzzles_list.append(pr)
            if ptype == "unlock" and first_unlock is None:
                first_unlock = pr
        out["puzzles"] = puzzles_list
        if first_unlock:
            out["puzzle"] = first_unlock
    return out


@router.get("/{game_id}/lore/audio")
async def get_lore_audio(game_id: str) -> Response:
    """Returns TTS audio of the room lore (Hebrew). Requires ELEVEN_API_KEY."""
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=GAME_NOT_FOUND_DETAIL)
    lore = game.get("room_lore") or ""
    if not lore:
        raise HTTPException(status_code=404, detail="אין סיפור רקע לחדר זה.")
    if not config.ELEVEN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="הקראת הסיפור אינה זמינה. הגדר ELEVEN_API_KEY.",
        )
    audio_bytes = generate_voice_over(lore, f"lore_{game_id}.mp3")
    if not audio_bytes:
        raise HTTPException(status_code=503, detail="יצירת האודיו נכשלה.")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/{game_id}/action")
async def game_action(game_id: str, payload: dict = Body(default_factory=dict)):
    """Submit a player action (unlock puzzle answer). Validation is server-side; correct answer from Redis (game state)."""
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=GAME_NOT_FOUND_DETAIL)
    item_id = (payload.get("item_id") or "").strip()
    answer = (payload.get("answer") or "").strip()
    puzzles = game.get("room_puzzles") or {}
    if not item_id or item_id not in puzzles:
        raise HTTPException(status_code=400, detail="פריט או חידה לא נמצאו.")
    p = puzzles[item_id]
    if (p.get("type") or "").lower() == "examine" or not p.get("correct_answer"):
        raise HTTPException(status_code=400, detail="משימה זו אינה דורשת שליחת תשובה.")
    correct_answer = (p.get("correct_answer") or "").strip()
    is_correct = normalize_answer(answer) == normalize_answer(correct_answer)
    message = SUCCESS_MESSAGE if is_correct else WRONG_MESSAGE
    return {"ok": True, "game_id": game_id, "correct": is_correct, "message": message}
