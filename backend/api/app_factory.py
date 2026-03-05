# pyright: reportMissingImports=false
"""Build FastAPI app: middleware, routers, root and webhook endpoints."""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

from config import config
from api.routes.games_routes import router as games_router
from api.routes.sse_game_routes import router as sse_game_router
from api.routes.pages_routes import router as pages_router
from api.routes.health_routes import router as health_router
from api.routes.media_routes import router as media_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Telegram Bot - חדר בריחה")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(games_router, prefix="/api")
    app.include_router(sse_game_router, prefix="/sse")
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
        if not hasattr(app.state, "tg_app"):
            logger.error("Webhook called before telegram app initialization")
            raise HTTPException(status_code=503, detail="Telegram app is not initialized")
        try:
            data = await request.json()
            update = Update.de_json(data=data, bot=app.state.tg_app.bot)
            await app.state.tg_app.update_queue.put(update)
        except Exception as e:
            logger.exception("Webhook processing failed: %s", e)
            raise HTTPException(status_code=500, detail="Webhook processing failed") from e
        return {"ok": True}

    return app
