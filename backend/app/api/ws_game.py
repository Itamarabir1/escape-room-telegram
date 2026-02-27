# pyright: reportMissingImports=false
"""WebSocket endpoint for per-game real-time events (e.g. puzzle_solved).

Handler is kept thin: auth and game loading are delegated to services.
Only registered players (in game['players']) can connect."""
import logging
from urllib.parse import parse_qs

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import HTTPException

from services.game_auth_service import get_game_and_user_for_ws
from services.ws_registry import register, unregister

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
    try:
        # מאמתים את המשתמש ומוודאים שהוא שחקן רשום במשחק
        game, user_id = get_game_and_user_for_ws(game_id, init_data)
        logger.debug("WebSocket auth ok for game_id=%s user_id=%s", game_id, user_id)
    except HTTPException as exc:
        # ממפים קודי HTTP לקודי WebSocket ייעודיים
        await websocket.accept()
        if exc.status_code == 404:
            await websocket.close(code=4404)  # Not Found
        else:
            await websocket.close(code=4403)  # Forbidden / Unauthorized
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
