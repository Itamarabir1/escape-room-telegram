# pyright: reportMissingImports=false
"""Pages controller: redirect to frontend."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse

from config import config


async def get_game_page(request: Request) -> RedirectResponse | dict[str, str]:
    if config.WEBAPP_URL:
        path = request.url.path
        query = request.url.query
        url = f"{config.WEBAPP_URL.rstrip('/')}{path}"
        if query:
            url += f"?{query}"
        return RedirectResponse(url=url, status_code=302)
    return {"detail": "WEBAPP_URL not set. Configure the frontend URL."}
