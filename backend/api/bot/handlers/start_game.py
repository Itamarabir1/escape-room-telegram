# pyright: reportMissingImports=false
"""Lobby system: /start_game (group-only), lobby_join, lobby_leaderboard, lobby_start."""
import logging
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from services.game_session import (
    start_registration,
    add_player,
    finish_registration,
    get_game_by_id,
    save_game,
    is_game_active,
)
from utils.urls import game_page_url
from infrastructure.redis.redis_client import redis_get_leaderboard_top10

logger = logging.getLogger(__name__)

LOBBY_HEADER = "🎮 חדר בריחה - לובי"


def _lobby_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✋ אני רוצה לשחק", callback_data="lobby_join")],
        [InlineKeyboardButton("🏆 עשרת הגדולים", callback_data="lobby_leaderboard")],
        [InlineKeyboardButton("🚀 כולם פה, נתחיל!", callback_data="lobby_start")],
    ])


def _lobby_empty_players_text() -> str:
    return "שחקנים שהצטרפו:\nעדיין אין שחקנים"


def _lobby_players_section(chat_data: dict) -> str:
    players = chat_data.get("players") or {}
    if not players:
        return _lobby_empty_players_text()
    return "שחקנים שהצטרפו:\n" + "\n".join(f"- {name}" for name in players.values())


async def start_game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or chat.type == "private":
        await update.message.reply_text("הפקודה פועלת רק בקבוצות. הוסף את הבוט לקבוצה והרץ /start_game שם.")
        return

    chat_data = context.chat_data
    start_registration(chat_data)
    chat_data["lobby_host_id"] = update.effective_user.id

    body = _lobby_empty_players_text()
    text = f"{LOBBY_HEADER}\n\n{body}"
    sent = await update.message.reply_text(text, reply_markup=_lobby_keyboard())
    chat_data["lobby_msg_id"] = sent.message_id


async def lobby_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    chat_data = context.chat_data

    if query.data == "lobby_join":
        if is_game_active(chat_data):
            await query.answer("המשחק כבר התחיל.", show_alert=False)
            return
        added = add_player(chat_data, user.id, user.first_name or "שחקן")
        if not added:
            await query.answer("כבר נרשמת 😄", show_alert=False)
            return
        await query.answer("נוספת למשחק! ✅", show_alert=False)
        if "lobby_msg_id" not in chat_data:
            return
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            return
        players_section = _lobby_players_section(chat_data)
        text = f"{LOBBY_HEADER}\n\n{players_section}"
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=chat_data["lobby_msg_id"],
                text=text,
                reply_markup=_lobby_keyboard(),
            )
        except BadRequest as e:
            logger.debug("lobby_join edit_message_text: %s", e)

    elif query.data == "lobby_leaderboard":
        top = redis_get_leaderboard_top10()
        if not top:
            await query.answer("אין עדיין שיאים 🏆", show_alert=True)
            return
        lines = []
        for i, (member, score) in enumerate(top, 1):
            sec = int(score)
            m, s = divmod(sec, 60)
            time_str = f"{m:02d}:{s:02d}"
            display = member if member.isdigit() is False else f"קבוצה {member}"
            lines.append(f"{i}. {display} — {time_str}")
        await query.answer("\n".join(lines), show_alert=True)

    elif query.data == "lobby_start":
        if user.id != chat_data.get("lobby_host_id"):
            await query.answer("רק מי שפתח את המשחק יכול להתחיל 🔒", show_alert=True)
            return
        players = chat_data.get("players") or {}
        if len(players) == 0:
            await query.answer("אין שחקנים רשומים עדיין!", show_alert=True)
            return
        chat_data["started_by_user_id"] = user.id
        chat = update.effective_chat
        chat_id = chat.id if chat else 0
        game_id = finish_registration(chat_id, chat_data)
        game = get_game_by_id(game_id)
        if game:
            game["started_at"] = datetime.now(timezone.utc).isoformat()
            save_game(game_id, game)
        game_url = game_page_url(game_id)
        if "lobby_msg_id" not in chat_data:
            await query.answer()
            return
        try:
            await query.edit_message_text(
                "✅ המשחק התחיל!\nבהצלחה לכולם 🚀",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎮 כנס למשחק", web_app=WebAppInfo(url=game_url))],
                ]),
            )
        except BadRequest as e:
            err_msg = getattr(e, "message", None) or str(e)
            if "button" in err_msg.lower():
                await query.edit_message_text(
                    "✅ המשחק התחיל!\nבהצלחה לכולם 🚀\n\nלחץ על הכפתור למטה:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎮 כנס למשחק", url=game_url)],
                    ]),
                )
            else:
                raise
        await query.answer()


def register_start_game_handler(application) -> None:
    application.add_handler(CommandHandler("start_game", start_game_cmd))
    application.add_handler(CallbackQueryHandler(lobby_callback, pattern="^lobby_"))
