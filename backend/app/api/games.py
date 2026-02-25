# pyright: reportMissingImports=false
"""Game API: state and actions for the Web App.
Frontend client (single place for all API calls): frontend/src/api/client.ts
Schema: domain.game.GameStateResponse

Architecture: Task content and correct answers live in backend (Redis game state).
Room image is not generated at runtime; use demo room (items + positions) or a static image later.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import FileResponse, Response

from config import config
from data.demo_room import (
    DEMO_ROOM_HEIGHT,
    DEMO_ROOM_ITEMS,
    DEMO_ROOM_META,
    DEMO_ROOM_PUZZLES,
    DEMO_ROOM_WIDTH,
)
from domain.game import GameStateResponse, PuzzleResponse
from domain.puzzle_status import PuzzleStatus
from services.game_session import end_game_by_id, get_game_by_id, save_game
from services.group_repository import set_finished_at
from services.ws_registry import broadcast_door_opened, broadcast_game_over, broadcast_puzzle_solved
from utils.puzzle import (
    SAFE_BACKSTORY,
    PROMPT_TEXT,
    SUCCESS_MESSAGE,
    WRONG_MESSAGE,
    normalize_answer,
)
from utils.telegram_webapp import get_user_id_from_validated, validate_init_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])

GAME_NOT_FOUND_DETAIL = "משחק לא נמצא או שהסתיים."
PLAYERS_ONLY_DETAIL = "רק מי שנרשם למשחק בקבוצה יכול להיכנס. פתחו את הלינק מההודעה בקבוצה."
INIT_DATA_REQUIRED_DETAIL = "פתחו את המשחק בלחיצה על הכפתור שמופיע בהודעה בקבוצה (כניסה למשחק או שחק עכשיו)."


def _get_game_and_require_player(game_id: str, request: Request) -> dict:
    """Load game. If no initData (e.g. opened via 'כניסה למשחק' link) allow access; else require registered player."""
    init_data = request.headers.get("X-Telegram-Init-Data") or ""
    if not init_data.strip():
        # נכנס מהלינק/כפתור רגיל – מאפשרים גישה בלי אימות (כדי שהכפתור "כניסה למשחק" יעבוד)
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
        raise HTTPException(status_code=403, detail=PLAYERS_ONLY_DETAIL)
    return game


def _apply_demo_room(game: dict) -> None:
    """Inject demo room items, puzzles, and static room image URL. State is saved to Redis."""
    base = config.base_url().rstrip("/")
    game["room_image_url"] = f"{base}/room/escape_room.png"
    game["room_image_width"] = DEMO_ROOM_WIDTH
    game["room_image_height"] = DEMO_ROOM_HEIGHT
    game["room_name"] = DEMO_ROOM_META["room_name"]
    game["room_description"] = DEMO_ROOM_META["room_description"]
    game["room_lore"] = DEMO_ROOM_META.get("room_lore", "")
    game["room_items"] = [dict(it) for it in DEMO_ROOM_ITEMS]
    game["room_puzzles"] = {}
    for item_id, p in DEMO_ROOM_PUZZLES.items():
        game["room_puzzles"][item_id] = dict(p)


@router.post("/{game_id}/start")
async def game_start(game_id: str, request: Request) -> dict:
    """Called when a user clicks 'התחל'. Records started_at so returning users rejoin with correct timer and no Start button."""
    game = _get_game_and_require_player(game_id, request)
    if not game.get("started_at"):
        game["started_at"] = datetime.now(timezone.utc).isoformat()
        save_game(game_id, game)
    return {"ok": True}


@router.post("/{game_id}/time_up")
async def game_time_up(game_id: str, request: Request) -> dict:
    """Called when the frontend timer reaches 0. Ends the game, broadcasts game_over via WebSocket, notifies the Telegram group."""
    game = _get_game_and_require_player(game_id, request)
    chat_id = game.get("chat_id")
    if chat_id is not None:
        set_finished_at(int(chat_id))
    end_game_by_id(game_id)
    await broadcast_game_over(game_id)
    if chat_id is not None:
        try:
            bot = getattr(request.app.state.tg_app, "bot", None)
            if bot:
                await bot.send_message(
                    chat_id=int(chat_id),
                    text="⏰ הזמן נגמר! Game Over.\n\nהמשחק הסתיים. כתבו /start_game כדי להתחיל מחדש.",
                )
        except Exception as e:
            logger.warning("Failed to send time-up message to group chat_id=%s: %s", chat_id, e)
    return {"ok": True, "message": "game_over"}


@router.get("/{game_id}")
async def get_game_state(game_id: str, request: Request) -> GameStateResponse:
    """Returns game state for Web App. When no room exists, applies fixed room (items + positions, no image). Image can be added later as static asset."""
    game = _get_game_and_require_player(game_id, request)

    needs_demo = (
        not game.get("room_image_url")
        or len(game.get("room_items") or []) < len(DEMO_ROOM_ITEMS)
        or not game.get("room_image_width")
    )
    if needs_demo:
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
            out["room_image_width"] = game.get("room_image_width") or DEMO_ROOM_WIDTH
            out["room_image_height"] = game.get("room_image_height") or DEMO_ROOM_HEIGHT
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
        room_solved = game.get("room_solved") or {}
        out["solved_item_ids"] = [
            iid for iid, status in room_solved.items()
            if status == PuzzleStatus.SOLVED.value
        ]
        if game.get("started_at"):
            out["started_at"] = game["started_at"]
    return out


def _needs_demo_room(game: dict) -> bool:
    """Same logic as in get_game_state: apply demo when room data is missing or incomplete."""
    return (
        not game.get("room_image_url")
        or len(game.get("room_items") or []) < len(DEMO_ROOM_ITEMS)
        or not game.get("room_image_width")
    )


# תיקיית שמע בפרויקט – האודיו נשמר כאן ומושמע בלחיצה על "התחל"
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = _BACKEND_DIR / "audio"
LORE_WAV_PATH = AUDIO_DIR / "lore.wav"


@router.get("/{game_id}/lore/audio")
async def get_lore_audio(game_id: str, request: Request) -> Response:
    """Serves the static lore audio (backend/audio/lore.wav). Played when user clicks התחל."""
    _get_game_and_require_player(game_id, request)
    if not LORE_WAV_PATH.exists():
        raise HTTPException(status_code=404, detail="Lore audio not found. Add backend/audio/lore.wav")
    return FileResponse(LORE_WAV_PATH, media_type="audio/wav")


def _item_label(game: dict, item_id: str) -> str:
    """Get display label for room item; fallback to item_id."""
    for it in game.get("room_items") or []:
        if it.get("id") == item_id:
            return (it.get("label") or item_id).strip()
    return item_id


@router.post("/{game_id}/action")
async def game_action(game_id: str, request: Request, payload: dict = Body(default_factory=dict)):
    """Submit a player action (unlock puzzle answer). Validation is server-side; correct answer from Redis (game state)."""
    game = _get_game_and_require_player(game_id, request)
    item_id = (payload.get("item_id") or "").strip()
    answer = (payload.get("answer") or "").strip()
    solver_name = (payload.get("solver_name") or "").strip() or None
    puzzles = game.get("room_puzzles") or {}
    if not item_id or item_id not in puzzles:
        raise HTTPException(status_code=400, detail="פריט או חידה לא נמצאו.")
    p = puzzles[item_id]
    if (p.get("type") or "").lower() == "examine" or not p.get("correct_answer"):
        raise HTTPException(status_code=400, detail="משימה זו אינה דורשת שליחת תשובה.")
    correct_answer = (p.get("correct_answer") or "").strip()
    aliases = p.get("correct_answer_aliases") or []
    accepted = [correct_answer] + [str(a).strip() for a in aliases if a is not None and str(a).strip()]
    normalized_user = normalize_answer(answer)
    is_correct = any(normalize_answer(a) == normalized_user for a in accepted)
    message = SUCCESS_MESSAGE if is_correct else WRONG_MESSAGE
    if is_correct:
        room_solved = game.get("room_solved") or {}
        room_solved[item_id] = PuzzleStatus.SOLVED.value
        game["room_solved"] = room_solved
        save_game(game_id, game)
        item_label = _item_label(game, item_id)
        await broadcast_puzzle_solved(
            game_id,
            item_id=item_id,
            item_label=item_label,
            answer=correct_answer,
            solver_name=solver_name,
        )
    return {"ok": True, "game_id": game_id, "correct": is_correct, "message": message}


def _all_unlock_puzzles_solved(game: dict) -> bool:
    """True if every unlock puzzle in room_puzzles is marked SOLVED in room_solved."""
    puzzles = game.get("room_puzzles") or {}
    room_solved = game.get("room_solved") or {}
    for item_id, p in puzzles.items():
        if (p.get("type") or "").lower() == "unlock":
            if room_solved.get(item_id) != PuzzleStatus.SOLVED.value:
                return False
    return True


@router.post("/{game_id}/door_opened")
async def door_opened(game_id: str, request: Request) -> dict:
    """Called when a player clicks the door after all puzzles are solved. Broadcasts door_opened to all clients so everyone plays the animation together."""
    game = _get_game_and_require_player(game_id, request)
    if not _all_unlock_puzzles_solved(game):
        raise HTTPException(status_code=400, detail="עדיין לא פתרתם את כל החידות בחדר.")
    await broadcast_door_opened(game_id)
    return {"ok": True}
