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
    logger.info("WS init_data present=%s game_id=%s", bool(init_data), game_id)
    try:
        game, user_id = get_game_and_user_for_ws(game_id, init_data)
        logger.debug("WebSocket auth ok for game_id=%s user_id=%s", game_id, user_id)
    except HTTPException as exc:
        await websocket.accept()
        if exc.status_code == 404:
            await websocket.close(code=4404)
        else:
            await websocket.close(code=4403)
        logger.info("WS auth rejected game_id=%s status=%s", game_id, exc.status_code)
        return

    await websocket.accept()
    logger.info("WS accepted game_id=%s user_id=%s", game_id, user_id)
    register(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        logger.info("WS disconnect game_id=%s", game_id)
        unregister(game_id, websocket)
