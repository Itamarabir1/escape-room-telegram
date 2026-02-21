# pyright: reportMissingImports=false
import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import config

# נתיב לקובץ ה-HTML של המשחק (יחסית למיקום הקובץ הזה)
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="Telegram Bot - חדר בריחה")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """שולח כפתור Web App לפתיחת המשחק."""
    web_app_url = config.WEBAPP_URL or "https://your-service-name.onrender.com"
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


@app.on_event("startup")
async def startup_event():
    tg_app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=os.getenv("ENV", "production") != "production",
    )