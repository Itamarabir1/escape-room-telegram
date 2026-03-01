# pyright: reportMissingImports=false
"""Application bootstrap: wires routers, webhook, static; starts bot on startup."""
import asyncio
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

from config.config import config
from infrastructure.database.session import init_db, wait_for_db
from api.routes.games_routes import router as games_router
from api.routes.ws_game_routes import router as ws_game_router
from api.routes.pages_routes import router as pages_router
from api.routes.health_routes import router as health_router
from api.routes.media_routes import router as media_router
from api.bot.app import create_telegram_app, run_telegram
from services.game_lifecycle_service import check_expired_games_loop

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Bot - חדר בריחה")

_origins = [
    config.WEBAPP_URL or config.FRONTEND_ORIGIN_FALLBACK,
    config.FRONTEND_ORIGIN_FALLBACK,
    "http://localhost:3000",
    "http://localhost:5173",
]
_origins = list(dict.fromkeys(_origins))
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router, prefix="/api")
app.include_router(ws_game_router, prefix="/ws")
app.include_router(pages_router)
app.include_router(health_router)
app.include_router(media_router)


@app.get("/")
async def root():
    return {"service": "escape-room-telegram-api", "docs": "/docs"}


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_well_known():
    return {}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data=data, bot=app.state.tg_app.bot)
        await app.state.tg_app.update_queue.put(update)
    except Exception as e:
        logger.exception("Webhook error: %s", e)
    return {"ok": True}


@app.on_event("startup")
async def startup_event():
    wait_for_db()
    init_db()
    tg_app = create_telegram_app()
    app.state.tg_app = tg_app
    asyncio.create_task(check_expired_games_loop())
    await run_telegram(tg_app)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.MODE != "production",
    )
