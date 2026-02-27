# pyright: reportMissingImports=false
"""Game API: state and actions for the Web App.
Frontend client (single place for all API calls): frontend/src/api/client.ts
Schema: domain.game.GameStateResponse

Architecture: Task content and correct answers live in backend (Redis game state).
Room image is not generated at runtime; use demo room (items + positions) or a static image later.
"""
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from domain.game import GameActionRequest, GameActionResponse, GameStateResponse
from services.game_api_service import (
    apply_demo_room,
    build_game_state_response,
    needs_demo_room,
)
from services.game_action_service import submit_puzzle_action
from services.game_auth_service import get_game_for_request
from services.game_lifecycle_service import (
    handle_door_opened as lifecycle_handle_door_opened,
    handle_time_up as lifecycle_handle_time_up,
    record_game_start,
)
from paths import LORE_WAV_PATH
from services.game_session import save_game

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/{game_id}/start")
async def game_start(game_id: str, request: Request) -> dict:
    """Called when a user clicks 'התחל'. Records started_at so returning users rejoin with correct timer and no Start button."""
    game = get_game_for_request(game_id, request)
    record_game_start(game_id, game)
    return {"ok": True}


@router.post("/{game_id}/time_up")
async def game_time_up(game_id: str, request: Request) -> dict:
    """Called when the frontend timer reaches 0. Ends the game, broadcasts game_over via WebSocket, notifies the Telegram group."""
    game = get_game_for_request(game_id, request)
    bot = getattr(request.app.state.tg_app, "bot", None)
    await lifecycle_handle_time_up(game_id, game, bot)
    return {"ok": True, "message": "game_over"}


@router.get("/{game_id}")
async def get_game_state(game_id: str, request: Request) -> GameStateResponse:
    """Returns game state for Web App. When no room exists, applies fixed room (items + positions, no image)."""
    game = get_game_for_request(game_id, request)
    if needs_demo_room(game):
        apply_demo_room(game)
        save_game(game_id, game)
        logger.info("Room applied for game_id=%s (items + positions, no image)", game_id)
    return build_game_state_response(game_id, game)


@router.get("/{game_id}/lore/audio")
async def get_lore_audio(game_id: str, request: Request) -> FileResponse:
    """Serves the static lore audio (backend/audio/lore.wav). Played when user clicks התחל."""
    get_game_for_request(game_id, request)
    if not LORE_WAV_PATH.exists():
        raise HTTPException(status_code=404, detail="Lore audio not found. Add backend/audio/lore.wav")
    return FileResponse(LORE_WAV_PATH, media_type="audio/wav")


@router.post("/{game_id}/action", response_model=GameActionResponse)
async def game_action(game_id: str, request: Request, body: GameActionRequest) -> GameActionResponse:
    """Submit a player action (unlock puzzle answer). Validation is server-side; correct answer from Redis (game state)."""
    game = get_game_for_request(game_id, request)
    result = await submit_puzzle_action(
        game_id,
        game,
        body.item_id,
        body.answer,
        body.solver_name,
    )
    return GameActionResponse(
        ok=True,
        game_id=game_id,
        correct=result["correct"],
        message=result["message"],
    )


@router.post("/{game_id}/door_opened")
async def door_opened(game_id: str, request: Request) -> dict:
    """Called when a player clicks the door after all puzzles are solved. Broadcasts door_opened to all clients so everyone plays the animation together."""
    game = get_game_for_request(game_id, request)
    await lifecycle_handle_door_opened(game_id, game)
    return {"ok": True}
