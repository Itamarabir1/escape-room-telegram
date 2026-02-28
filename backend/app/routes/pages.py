# pyright: reportMissingImports=false
"""Redirects /game to the frontend (WEBAPP_URL). Health is in routes/health.py."""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi import Request

from config import config

router = APIRouter(tags=["pages"])


@router.get("/game")
async def get_game(request: Request):
    """Redirect to the frontend Web App URL (game is served by the frontend container)."""
    if config.WEBAPP_URL:
        path = request.url.path
        query = request.url.query
        url = f"{config.WEBAPP_URL.rstrip('/')}{path}"
        if query:
            url += f"?{query}"
        return RedirectResponse(url=url, status_code=302)
    return {"detail": "WEBAPP_URL not set. Configure the frontend URL."}
