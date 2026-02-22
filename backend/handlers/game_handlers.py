# pyright: reportMissingImports=false
"""Telegram handlers for group game: /start_game, join, מתחילים, /end_game. Thin layer over services."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import config
from services.game_session import (
    start_registration,
    add_player,
    is_game_active,
    get_players_list_text,
    finish_registration,
    end_game_chat,
)


def register_game_handlers(application):
    application.add_handler(CommandHandler("start_game", start_game))
    application.add_handler(CommandHandler("end_game", end_game))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_any_message))


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = context.chat_data
    if is_game_active(chat_data):
        await update.message.reply_text("המשחק כבר התחיל! אי אפשר להירשם שוב כרגע. ✋")
        return

    start_registration(chat_data)
    keyboard = [[InlineKeyboardButton("אני רוצה לשחק! 🙋‍♂️", callback_data="join_game")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent = await update.message.reply_text(
        "🎮 **ההרפתקה מתחילה!**\n\nמי מצטרף אלינו היום? לחצו על הכפתור למטה כדי להירשם.",
        reply_markup=reply_markup,
    )
    chat_data["registration_msg_id"] = sent.message_id


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_data = context.chat_data

    if query.data == "join_game":
        if is_game_active(chat_data):
            game_id = chat_data.get("game_id")
            if game_id:
                await query.answer()
                web_app_url = (config.WEBAPP_URL or "").strip().rstrip("/") or "https://escape-room-telegram.onrender.com"
                game_url = f"{web_app_url}/game?game_id={game_id}"
                keyboard = [[InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=game_url))]]
                await query.message.reply_text(
                    "ההרשמה נסגרה. לחץ על הכפתור למטה כדי להיכנס למשחק:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await query.answer(
                    "מצטערים, ההרשמה נסגרה. חפש בקבוצה את ההודעה עם הכפתור 'שחק עכשיו'.",
                    show_alert=True,
                )
            return
        if not add_player(chat_data, user.id, user.first_name or "שחקן"):
            await query.answer("אתה כבר רשום למשחק! 😉", show_alert=True)
            return
        await query.answer()
        players_list = get_players_list_text(chat_data)
        keyboard = [
            [InlineKeyboardButton("גם אני רוצה! 🙋‍♂️", callback_data="join_game")],
            [InlineKeyboardButton("כולם פה, אפשר להתחיל! 🚀", callback_data="start_ai_story")],
        ]
        await query.edit_message_text(
            f"🎮 **רשימת שחקנים מעודכנת:**\n{players_list}\n\n"
            "מחכים שכולם יירשמו... כשתהיו מוכנים, לחצו על הכפתור למטה!",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "start_ai_story":
        if is_game_active(chat_data):
            # שולח כפתור "שחק עכשיו" בהודעה חדשה – כך ברור איפה ללחוץ (גם אם עריכת ההודעה הקודמת נכשלה)
            game_id = chat_data.get("game_id")
            if game_id:
                await query.answer()
                web_app_url = (config.WEBAPP_URL or "").strip().rstrip("/") or "https://escape-room-telegram.onrender.com"
                game_url = f"{web_app_url}/game?game_id={game_id}"
                keyboard = [[InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=game_url))]]
                await query.message.reply_text(
                    "המשחק כבר התחיל. לחץ על הכפתור למטה כדי להיכנס:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await query.answer(
                    "המשחק כבר התחיל. חפש בקבוצה את ההודעה עם הכפתור 'שחק עכשיו' ולחץ עליו.",
                    show_alert=True,
                )
            return
        try:
            chat_id = update.effective_chat.id if update.effective_chat else 0
            game_id = finish_registration(chat_id, chat_data)
            web_app_url = (config.WEBAPP_URL or "").strip().rstrip("/")
            if not web_app_url:
                logging.warning("WEBAPP_URL not set; Web App button may not work. Set it in .env or Render Environment.")
                web_app_url = "https://escape-room-telegram.onrender.com"
            game_url = f"{web_app_url}/game?game_id={game_id}"
            keyboard = [
                [InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=game_url))],
            ]
            await query.answer()
            await query.edit_message_text(
                "🎲 ההרשמה נסגרה! לחצו על הכפתור למטה כדי להיכנס לאותו משחק משותף.",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            logging.exception("Error in start_ai_story callback: %s", e)
            await query.answer("אירעה שגיאה. נסה שוב או שלח /end_game ואז /start_game.", show_alert=True)

    elif query.data == "ignore_welcome":
        await query.answer()
        await query.edit_message_text("אולי פעם אחרת! המשך יום נעים. 😊")


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_user in update.message.new_chat_members:
        if new_user.is_bot:
            continue
        keyboard = [
            [
                InlineKeyboardButton("כן ✅", callback_data="join_game"),
                InlineKeyboardButton("לא ❌", callback_data="ignore_welcome"),
            ]
        ]
        await update.message.reply_text(
            f"אהלן {new_user.first_name}! רוצה להצטרף למשחק?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = context.chat_data
    if not is_game_active(chat_data):
        await update.message.reply_text("אין משחק פעיל כרגע שאפשר לסיים! 😊")
        return
    end_game_chat(chat_data)
    await update.message.reply_text(
        "🏆 **המשחק הסתיים!**\n"
        "מקווים שנהניתם. עכשיו אפשר להתחיל הרפתקה חדשה עם פקודת /start_game."
    )
