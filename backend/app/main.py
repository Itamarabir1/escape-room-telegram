# pyright: reportMissingImports=false
"""Presentation entrypoint: wires routers, webhook, static; starts bot on startup. See ARCHITECTURE.md."""
import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from telegram import Update

from config import config
from app.api.games import router as games_router
from app.api.ws_game import router as ws_game_router
from app.routes.pages import router as pages_router
from app.routes.health import router as health_router
from app.bot.app import create_telegram_app, run_telegram

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Bot - חדר בריחה")

# Repo root: telegram-bot/; backend at telegram-bot/backend/
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
IMAGES_DIR = _REPO_ROOT / "images"
AUDIO_DIR = _BACKEND_DIR / "audio"
FRONTEND_DIST = _REPO_ROOT / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST)), name="static")
else:
    logger.warning("frontend/dist not found; run 'cd frontend && npm run build'. /static and /game will not serve frontend.")


@app.get("/room/escape_room.png")
async def serve_room_image():
    """Serves the static room image from project images folder (escape_room.png)."""
    path = IMAGES_DIR / "escape_room.png"
    if not path.exists():
        candidates = sorted(IMAGES_DIR.glob("escape_room_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        path = candidates[0] if candidates else None
    if not path or not path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Room image not found. Add images/escape_room.png")
    return FileResponse(path, media_type="image/png")


@app.get("/room/door_open.mp4")
async def serve_door_video():
    """Serves the door opening video from project images folder (door_open.mp4 or door-opening.mp4)."""
    for name in ("door_open.mp4", "door-opening.mp4"):
        path = IMAGES_DIR / name
        if path.exists():
            return FileResponse(path, media_type="video/mp4")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Door video not found. Add images/door_open.mp4")


@app.get("/audio/lore.wav")
async def serve_lore_audio():
    """Serves the static lore audio (backend/audio/lore.wav). Used when user clicks התחל."""
    path = AUDIO_DIR / "lore.wav"
    if not path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lore audio not found. Add backend/audio/lore.wav")
    return FileResponse(path, media_type="audio/wav")


app.include_router(games_router, prefix="/api")
app.include_router(ws_game_router, prefix="/ws")
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
