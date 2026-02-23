# pyright: reportMissingImports=false
"""In-memory registry of WebSocket connections per game_id for real-time puzzle_solved broadcast."""
import json
import logging
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)

# game_id -> set of WebSocket connections (only that game's clients receive events)
_connections: dict[str, set[WebSocket]] = {}


def register(game_id: str, ws: WebSocket) -> None:
    """Add a WebSocket to the set for this game_id."""
    if game_id not in _connections:
        _connections[game_id] = set()
    _connections[game_id].add(ws)
    logger.debug("WS registered game_id=%s total=%s", game_id, len(_connections[game_id]))


def unregister(game_id: str, ws: WebSocket) -> None:
    """Remove a WebSocket from the set for this game_id."""
    if game_id in _connections:
        _connections[game_id].discard(ws)
        if not _connections[game_id]:
            del _connections[game_id]
    logger.debug("WS unregistered game_id=%s", game_id)


async def broadcast_puzzle_solved(
    game_id: str,
    *,
    item_id: str,
    item_label: str,
    answer: str,
    solver_name: str | None = None,
) -> None:
    """Send puzzle_solved event to all connections for this game_id. Skips closed connections."""
    payload: dict[str, Any] = {
        "event": "puzzle_solved",
        "item_id": item_id,
        "item_label": item_label,
        "answer": answer,
    }
    if solver_name:
        payload["solver_name"] = solver_name
    text = json.dumps(payload, ensure_ascii=False)
    if game_id not in _connections:
        return
    dead: set[WebSocket] = set()
    for ws in _connections[game_id]:
        try:
            await ws.send_text(text)
        except Exception as e:
            logger.debug("WS send failed game_id=%s: %s", game_id, e)
            dead.add(ws)
    for ws in dead:
        unregister(game_id, ws)


async def broadcast_game_over(game_id: str) -> None:
    """Send game_over event to all connections for this game (e.g. timer expired)."""
    payload: dict[str, Any] = {"event": "game_over"}
    text = json.dumps(payload, ensure_ascii=False)
    if game_id not in _connections:
        return
    dead: set[WebSocket] = set()
    for ws in _connections[game_id]:
        try:
            await ws.send_text(text)
        except Exception as e:
            logger.debug("WS game_over send failed game_id=%s: %s", game_id, e)
            dead.add(ws)
    for ws in dead:
        unregister(game_id, ws)
