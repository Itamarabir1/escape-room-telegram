"""Game API routes: endpoint definitions only. Delegates to games.controller."""
from fastapi import APIRouter, Request

from schemas.game_schema import GameActionRequest, GameActionResponse
from domain.game import GameStateResponse
from api.controllers.games_controller import (
    game_start as _game_start,
    game_time_up as _game_time_up,
    get_game_state as _get_game_state,
    get_lore_audio as _get_lore_audio,
    game_action as _game_action,
    door_opened as _door_opened,
)

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/{game_id}/start")
async def game_start(game_id: str, request: Request) -> dict:
    return await _game_start(game_id, request)


@router.post("/{game_id}/time_up")
async def game_time_up(game_id: str, request: Request) -> dict:
    return await _game_time_up(game_id, request)


@router.get("/{game_id}")
async def get_game_state(game_id: str, request: Request) -> GameStateResponse:
    return await _get_game_state(game_id, request)


@router.get("/{game_id}/lore/audio")
async def get_lore_audio(game_id: str, request: Request):
    return await _get_lore_audio(game_id, request)


@router.post("/{game_id}/action", response_model=GameActionResponse)
async def game_action(game_id: str, request: Request, body: GameActionRequest) -> GameActionResponse:
    return await _game_action(game_id, request, body)


@router.post("/{game_id}/door_opened")
async def door_opened(game_id: str, request: Request) -> dict:
    return await _door_opened(game_id, request)
