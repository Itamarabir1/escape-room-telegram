# pyright: reportMissingImports=false
"""Presentation entrypoint: wires routers, webhook, static; starts bot on startup. See ARCHITECTURE.md."""
import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from telegram import Update

from config import config
from app.api.games import router as games_router
from app.routes.pages import router as pages_router
from app.routes.health import router as health_router
from app.bot.app import create_telegram_app, run_telegram

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Bot - חדר בריחה")

# Frontend build output only (no source). telegram-bot/frontend/dist; backend at telegram-bot/backend/
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = _REPO_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST)), name="static")
else:
    logger.warning("frontend/dist not found; run 'cd frontend && npm run build'. /static and /game will not serve frontend.")

app.include_router(games_router, prefix="/api")
app.include_router(pages_router)
app.include_router(health_router)


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_well_known():
    """Chrome DevTools probes this; return empty so we don't log 404."""
    return {}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Receives updates from Telegram (production)."""
    try:
        data = await request.json()
        update = Update.de_json(data=data, bot=app.state.tg_app.bot)
        await app.state.tg_app.update_queue.put(update)
    except Exception as e:
        logger.exception("Webhook error: %s", e)
    return {"ok": True}


@app.on_event("startup")
async def startup_event():
    tg_app = create_telegram_app()
    app.state.tg_app = tg_app
    await run_telegram(tg_app)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.MODE != "production",
    )
