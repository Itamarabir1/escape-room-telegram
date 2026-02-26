# pyright: reportMissingImports=false
"""WebSocket endpoint for per-game real-time events (e.g. puzzle_solved). Only registered players can connect."""
import logging
from urllib.parse import parse_qs

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from config import config
from services.game_session import get_game_by_id
from services.ws_registry import register, unregister
from utils.telegram_webapp import get_user_id_from_validated, validate_init_data

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_init_data_from_scope(scope: dict) -> str:
    """Extract init_data from WebSocket query string."""
    query = scope.get("query_string") or b""
    if isinstance(query, bytes):
        query = query.decode("utf-8", errors="replace")
    parsed = parse_qs(query)
    return (parsed.get("init_data") or [""])[0]


@router.websocket("/games/{game_id}")
async def ws_games(websocket: WebSocket, game_id: str) -> None:
    """Connect to receive real-time events for this game. Only registered players (in game['players']) can connect."""
    init_data = _get_init_data_from_scope(websocket.scope)
    token = config.TELEGRAM_TOKEN or ""
    validated = validate_init_data(init_data, token) if init_data else None
    user_id = get_user_id_from_validated(validated) if validated else None
    game = get_game_by_id(game_id)
    if not game:
        await websocket.accept()
        await websocket.close(code=4404)  # Not Found
        return
    if user_id is None or str(user_id) not in (game.get("players") or {}):
        await websocket.accept()
        await websocket.close(code=4403)  # Forbidden
        return
    await websocket.accept()
    register(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unregister(game_id, websocket)
