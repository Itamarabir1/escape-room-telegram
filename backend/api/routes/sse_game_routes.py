# pyright: reportMissingImports=false
"""SSE routes: endpoint definitions only."""
from fastapi import APIRouter, Request

from api.controllers.sse_controller import sse_games_handler

router = APIRouter()


@router.get("/games/{game_id}")
async def sse_games(request: Request, game_id: str):
    return await sse_games_handler(request, game_id)
