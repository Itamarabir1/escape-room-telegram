# pyright: reportMissingImports=false
"""In-memory registry of SSE subscribers per game_id for real-time game events."""
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# game_id -> list of subscriber queues (only that game's clients receive events)
_connections: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}


def register(game_id: str) -> asyncio.Queue[dict[str, Any]]:
    """Create and register a queue subscriber for this game_id."""
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    if game_id not in _connections:
        _connections[game_id] = []
    _connections[game_id].append(queue)
    n = len(_connections[game_id])
    logger.debug("SSE registered game_id=%s total=%s", game_id, n)
    logger.info("SSE register game_id=%s connections_count=%s", game_id, n)
    return queue


def unregister(game_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
    """Remove a queue subscriber from this game_id."""
    n = 0
    if game_id in _connections:
        try:
            _connections[game_id].remove(queue)
        except ValueError:
            pass
        if not _connections[game_id]:
            del _connections[game_id]
            n = 0
        else:
            n = len(_connections[game_id])
    logger.debug("SSE unregistered game_id=%s", game_id)
    logger.info("SSE unregister game_id=%s connections_count=%s", game_id, n)


async def _broadcast(game_id: str, payload: dict[str, Any]) -> None:
    """Push payload to all subscriber queues for this game_id."""
    if game_id not in _connections:
        logger.info("SSE broadcast game_id=%s skipped no_connections", game_id)
        return
    conn_count = len(_connections[game_id])
    logger.info(
        "SSE broadcast game_id=%s connections=%s payload_type=%s",
        game_id,
        conn_count,
        payload.get("type") or payload.get("event"),
    )
    dead_count = 0
    for queue in list(_connections[game_id]):
        try:
            queue.put_nowait(payload)
        except Exception as e:
            dead_count += 1
            logger.info("SSE enqueue failed game_id=%s err=%s", game_id, e)
            unregister(game_id, queue)
    if dead_count:
        logger.info(
            "SSE broadcast pruning_dead game_id=%s dead_count=%s",
            game_id,
            dead_count,
        )


async def broadcast_puzzle_solved(
    game_id: str,
    *,
    item_id: str,
    item_label: str,
    answer: str,
    solver_name: str | None = None,
) -> None:
    """Send puzzle_solved event to all subscribers for this game_id."""
    payload: dict[str, Any] = {
        "event": "puzzle_solved",
        "item_id": item_id,
        "item_label": item_label,
        "answer": answer,
    }
    if solver_name:
        payload["solver_name"] = solver_name
    await _broadcast(game_id, payload)


async def broadcast_game_over(game_id: str, reason: str = "timeout") -> None:
    """Send game_over event to all subscribers for this game."""
    await _broadcast(game_id, {"type": "game_over", "reason": reason})


async def broadcast_game_started(game_id: str, started_at: str) -> None:
    """Notify all subscribers that game start was recorded."""
    await _broadcast(game_id, {"type": "game_started", "started_at": started_at})


async def broadcast_door_opened(game_id: str) -> None:
    """Send door_opened event to all subscribers for this game."""
    await _broadcast(game_id, {"event": "door_opened"})
