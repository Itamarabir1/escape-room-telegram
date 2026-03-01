# pyright: reportMissingImports=false
"""Health controller: return status and mode."""
from fastapi.responses import JSONResponse

from config.config import config

HEALTH_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate"}


async def health_check() -> JSONResponse:
    return JSONResponse(
        content={"status": "awake", "mode": config.MODE},
        headers=HEALTH_HEADERS,
    )
