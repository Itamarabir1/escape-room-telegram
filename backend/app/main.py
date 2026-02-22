# pyright: reportMissingImports=false
import logging
import os
from pathlib import Path

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import config

logger = logging.getLogger(__name__)

# נתיב לקובץ ה-HTML של המשחק (יחסית למיקום הקובץ הזה)
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="Telegram Bot - חדר בריחה")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """שולח כפתור Web App לפתיחת המשחק."""
    web_app_url = config.WEBAPP_URL or "https://escape-room-telegram.onrender.com"
    game_url = f"{web_app_url}/game"

    keyboard = [
        [InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=game_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "ברוך הבא למשחק! לחץ על הכפתור למטה כדי להתחיל:",
        reply_markup=reply_markup,
    )


@app.get("/game")
async def get_game():
    """מגיש את דף המשחק (Web App)."""
    if not INDEX_HTML.exists():
        return {"detail": "קובץ המשחק לא נמצא. ודא ש-backend/app/static/index.html קיים."}
    return FileResponse(INDEX_HTML)


@app.get("/health")
async def health():
    """בדיקת חיים ל-Render."""
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """מקבל עדכונים מטלגרם (Webhook) – ב-Production טלגרם שולחת לכאן במקום Polling."""
    try:
        data = await request.json()
        update = Update.de_json(data=data, bot=app.state.tg_app.bot)
        await app.state.tg_app.update_queue.put(update)
    except Exception as e:
        logger.exception("Webhook error: %s", e)
    return {"ok": True}


# --- Game API for Web App (shared game state by game_id) ---
@app.get("/api/games/{game_id}")
async def get_game_state(game_id: str):
    """Returns game state for Web App: players, game_active. Used so all clients see same game."""
    from services.game_session import get_game_by_id
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="משחק לא נמצא או שהסתיים.")
    return {
        "game_id": game_id,
        "players": game.get("players", {}),
        "game_active": game.get("game_active", True),
    }


@app.post("/api/games/{game_id}/action")
async def game_action(game_id: str, payload: dict = Body(default_factory=dict)):
    """Submit a player action (e.g. from Web App). Validates game_id and optional user_id."""
    from services.game_session import get_game_by_id
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="משחק לא נמצא או שהסתיים.")
    # Placeholder: accept any action; later wire to LogicEngine / story_engine
    return {"ok": True, "game_id": game_id}


@app.on_event("startup")
async def startup_event():
    tg_app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    from handlers.game_handlers import register_game_handlers
    register_game_handlers(tg_app)
    await tg_app.initialize()
    await tg_app.start()
    app.state.tg_app = tg_app

    base_url = (config.WEBAPP_URL or "").strip().rstrip("/")
    if base_url:
        # Production: טלגרם תשלח עדכונים ל-Webhook. אסור להריץ Polling (getUpdates) Webhook פעיל.
        webhook_url = f"{base_url}/webhook"
        await tg_app.bot.set_webhook(url=webhook_url)
        logger.info("Webhook set: %s", webhook_url)
    else:
        # פיתוח לוקאלי: Polling (getUpdates)
        await tg_app.updater.start_polling()
        logger.info("Polling started (no WEBAPP_URL)")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=os.getenv("ENV", "production") != "production",
    )