# pyright: reportMissingImports=false
"""SSE controller: auth and stream lifecycle. Delegates event fanout to sse_registry."""
import asyncio
import json
import logging
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse

from services.game_auth_service import get_game_and_user_for_ws
from services.sse_registry import register, unregister

logger = logging.getLogger(__name__)


def get_init_data_from_request(request: Request) -> str:
    query = request.url.query or ""
    parsed = parse_qs(query)
    return (parsed.get("init_data") or [""])[0]


def _sse_format(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def sse_games_handler(request: Request, game_id: str) -> StreamingResponse:
    init_data = get_init_data_from_request(request)
    logger.info("SSE init_data present=%s game_id=%s", bool(init_data), game_id)
    try:
        _, user_id = get_game_and_user_for_ws(game_id, init_data)
        logger.debug("SSE auth ok for game_id=%s user_id=%s", game_id, user_id)
    except HTTPException as exc:
        logger.info(
            "SSE auth rejected game_id=%s status=%s init_data_present=%s",
            game_id,
            exc.status_code,
            bool(init_data),
        )
        raise

    queue = register(game_id)

    async def event_stream():
        try:
            # Initial heartbeat frame so client receives headers+body immediately.
            yield ": connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield _sse_format(payload)
                except asyncio.TimeoutError:
                    # Keep connection active through idle periods.
                    yield ": keepalive\n\n"
        finally:
            logger.info("SSE disconnect game_id=%s user_id=%s", game_id, user_id)
            unregister(game_id, queue)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
