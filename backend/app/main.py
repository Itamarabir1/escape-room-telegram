# pyright: reportMissingImports=false
"""Presentation entrypoint: wires routers, webhook, static; starts bot on startup. See ARCHITECTURE.md."""
import logging

import uvicorn
from fastapi import FastAPI, Request
from telegram import Update

from config import config
from db import init_db
from app.api.games import router as games_router
from app.api.ws_game import router as ws_game_router
from app.routes.pages import router as pages_router
from app.routes.health import router as health_router
from app.routes.media import router as media_router
from app.bot.app import create_telegram_app, run_telegram

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Bot - חדר בריחה")

app.include_router(games_router, prefix="/api")
app.include_router(ws_game_router, prefix="/ws")
app.include_router(pages_router)
app.include_router(health_router)
app.include_router(media_router)


@app.get("/")
async def root():
    """Root path: API only; no redirect. Frontend (escape-room-telegram) serves the app."""
    return {"service": "escape-room-telegram-api", "docs": "/docs"}


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
    init_db()
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
