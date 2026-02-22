# pyright: reportMissingImports=false
"""Health check endpoint – for external scripts and load balancers (e.g. Render)."""
from fastapi import APIRouter

from config import config
from domain.game import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> HealthResponse:
    """Called by external scripts / Render. Returns status and mode."""
    return {"status": "awake", "mode": config.MODE}
