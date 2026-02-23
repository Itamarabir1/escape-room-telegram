# pyright: reportMissingImports=false
"""Health and keep-alive – for Render health check and Cron-job.org (keeps free instance awake)."""
from fastapi import APIRouter

from config import config
from domain.game import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Render health check + Cron-job.org keep-alive.
    For Cron-job.org: ping this URL every 14 minutes. Example: https://escape-room-telegram.onrender.com/health
    """
    return {"status": "awake", "mode": config.MODE}
