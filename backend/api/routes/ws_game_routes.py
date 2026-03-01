# pyright: reportMissingImports=false
"""WebSocket routes: endpoint definitions only."""
from fastapi import APIRouter, WebSocket

from api.controllers.ws_game_controller import ws_games_handler

router = APIRouter()


@router.websocket("/games/{game_id}")
async def ws_games(websocket: WebSocket, game_id: str) -> None:
    await ws_games_handler(websocket, game_id)
