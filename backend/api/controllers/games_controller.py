# pyright: reportMissingImports=false
"""Game API controller: request parsing, call services, return response. No business logic."""
import logging

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from domain.game import GameStateResponse
from schemas.game_schema import GameActionRequest, GameActionResponse
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
from config.paths import LORE_WAV_PATH
from services.game_session import save_game
from services.ws_registry import broadcast_game_started

logger = logging.getLogger(__name__)


async def game_start(game_id: str, request: Request) -> dict:
    game = get_game_for_request(game_id, request)
    had_started = bool(game.get("started_at"))
    record_game_start(game_id, game)
    if not had_started and game.get("started_at"):
        await broadcast_game_started(game_id, game["started_at"])
    return {"started_at": game["started_at"]}


async def game_time_up(game_id: str, request: Request) -> dict:
    game = get_game_for_request(game_id, request)
    bot = getattr(request.app.state.tg_app, "bot", None)
    await lifecycle_handle_time_up(game_id, game, bot)
    return {"ok": True, "message": "game_over"}


async def get_game_state(game_id: str, request: Request) -> GameStateResponse:
    game = get_game_for_request(game_id, request)
    if needs_demo_room(game):
        apply_demo_room(game)
        save_game(game_id, game)
        logger.info("Room applied for game_id=%s (items + positions, no image)", game_id)
    return build_game_state_response(game_id, game)


async def get_lore_audio(game_id: str, request: Request) -> FileResponse:
    get_game_for_request(game_id, request)
    if not LORE_WAV_PATH.exists():
        raise HTTPException(status_code=404, detail="Lore audio not found. Add backend/audio/lore.wav")
    return FileResponse(LORE_WAV_PATH, media_type="audio/wav")


async def game_action(game_id: str, request: Request, body: GameActionRequest) -> GameActionResponse:
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


async def door_opened(game_id: str, request: Request) -> dict:
    game = get_game_for_request(game_id, request)
    await lifecycle_handle_door_opened(game_id, game)
    return {"ok": True}
