# pyright: reportMissingImports=false
"""WebSocket controller: auth and connection lifecycle. Delegates to services."""
import logging
from urllib.parse import parse_qs

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from services.game_auth_service import get_game_and_user_for_ws
from services.ws_registry import register, unregister

logger = logging.getLogger(__name__)


def get_init_data_from_scope(scope: dict) -> str:
    query = scope.get("query_string") or b""
    if isinstance(query, bytes):
        query = query.decode("utf-8", errors="replace")
    parsed = parse_qs(query)
    return (parsed.get("init_data") or [""])[0]


async def ws_games_handler(websocket: WebSocket, game_id: str) -> None:
    init_data = get_init_data_from_scope(websocket.scope)
    try:
        game, user_id = get_game_and_user_for_ws(game_id, init_data)
        logger.debug("WebSocket auth ok for game_id=%s user_id=%s", game_id, user_id)
    except HTTPException as exc:
        await websocket.accept()
        if exc.status_code == 404:
            await websocket.close(code=4404)
        else:
            await websocket.close(code=4403)
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
