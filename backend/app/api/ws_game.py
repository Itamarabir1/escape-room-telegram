# pyright: reportMissingImports=false
"""WebSocket endpoint for per-game real-time events (e.g. puzzle_solved)."""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.game_session import get_game_by_id
from services.ws_registry import register, unregister

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/games/{game_id}")
async def ws_games(websocket: WebSocket, game_id: str) -> None:
    """Connect to receive real-time events for this game. Only clients in this game receive puzzle_solved."""
    await websocket.accept()
    game = get_game_by_id(game_id)
    if not game:
        await websocket.close(code=4404)
        return
    register(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unregister(game_id, websocket)
