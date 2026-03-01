# pyright: reportMissingImports=false
""" /start command: sends Web App button to open the game."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler

from utils.urls import game_app_url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game_url = game_app_url()
    keyboard = [[InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=game_url))]]
    await update.message.reply_text(
        "ברוך הבא למשחק! לחץ על הכפתור למטה כדי להתחיל:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def register_start_handler(application):
    application.add_handler(CommandHandler("start", start))
