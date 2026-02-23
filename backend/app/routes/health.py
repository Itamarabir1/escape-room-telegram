# pyright: reportMissingImports=false
"""Health and keep-alive – for Render health check and Cron-job.org (keeps free instance awake)."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import config

router = APIRouter(tags=["health"])

# מונע cache – כדי ש-Cron/Render יקבלו תגובה עדכנית ולא cache של CDN/דפדפן
HEALTH_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate"}


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Render health check + Cron-job.org keep-alive.
    - Cron-job.org: GET לכתובת הזו כל 14 דקות (פחות מ-15 כדי למנוע sleep).
    - Timeout ב-Cron: לפחות 60 שניות (אחרי sleep הבקשה הראשונה לוקחת ~50 שניות).
    """
    return JSONResponse(
        content={"status": "awake", "mode": config.MODE},
        headers=HEALTH_HEADERS,
    )
