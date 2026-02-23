# pyright: reportMissingImports=false
"""Group game: /start_game, join, מתחילים, /end_game. Thin layer over game_session."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from services.game_session import (
    start_registration,
    add_player,
    is_game_active,
    get_players_list_text,
    finish_registration,
    end_game_chat,
    get_game_by_id,
)
from services.player_repository import register_player as register_player_db
from utils.urls import game_page_url

logger = logging.getLogger(__name__)

# --- Helpers: send game link as button or plain text ---


async def send_game_button_or_link(message, game_id: str, intro: str) -> None:
    """Sends Web App button; on Button_type_invalid falls back to plain link."""
    url = game_page_url(game_id)
    keyboard = [[InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=url))]]
    try:
        await message.reply_text(intro, reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest as e:
        err_msg = getattr(e, "message", None) or str(e)
        if "button" in err_msg.lower():
            await message.reply_text(f"{intro}\n{url}")
        else:
            raise


async def send_fallback_game_link(query, chat_data: dict) -> None:
    """On error: send plain game link only (no button retry)."""
    game_id = chat_data.get("game_id")
    if not game_id:
        await query.message.reply_text("אירעה שגיאה בהתחלת המשחק. נסה /end_game ואז /start_game.")
        return
    await query.message.reply_text(f"המשחק מוכן. פתח את הלינק כדי להיכנס:\n{game_page_url(game_id)}")


# --- Handlers ---


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    if is_game_active(chat_data):
        game_id = chat_data.get("game_id")
        if game_id and get_game_by_id(game_id) is None:
            end_game_chat(chat_data)
        else:
            await update.message.reply_text("המשחק כבר התחיל! אי אפשר להירשם שוב כרגע. ✋")
            return
    start_registration(chat_data)
    keyboard = [[InlineKeyboardButton("אני רוצה לשחק! 🙋‍♂️", callback_data="join_game")]]
    sent = await update.message.reply_text(
        "🎮 **ההרפתקה מתחילה!**\n\nמי מצטרף אלינו היום? לחצו על הכפתור למטה כדי להירשם.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    chat_data["registration_msg_id"] = sent.message_id


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    chat_data = context.chat_data
    logger.debug("callback data=%s chat_id=%s", query.data, update.effective_chat.id if update.effective_chat else None)

    if query.data == "join_game":
        if is_game_active(chat_data):
            game_id = chat_data.get("game_id")
            if game_id:
                await query.answer()
                await send_game_button_or_link(
                    query.message, game_id,
                    "ההרשמה נסגרה. לחץ על הכפתור למטה כדי להיכנס למשחק:",
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
        chat_id = update.effective_chat.id if update.effective_chat else 0
        if chat_id:
            register_player_db(chat_id, user.id, user.first_name or "שחקן")
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
        logger.debug("start_ai_story chat_id=%s game_active=%s", update.effective_chat.id if update.effective_chat else None, is_game_active(chat_data))
        if is_game_active(chat_data):
            game_id = chat_data.get("game_id")
            if game_id:
                await query.answer()
                await send_game_button_or_link(
                    query.message, game_id,
                    "המשחק כבר התחיל. לחץ על הכפתור למטה כדי להיכנס:",
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
            await query.answer()
            await send_game_button_or_link(
                query.message, game_id,
                "🎲 ההרשמה נסגרה!\n\nלחץ על הכפתור \"שחק עכשיו\" למטה – ייפתח דף המשחק בדפדפן.",
            )
        except BadRequest as e:
            logger.exception("Telegram BadRequest in start_ai_story: %s", getattr(e, "message", str(e)))
            try:
                await query.answer("שגיאה מהטלגרם. נסה /end_game ואז /start_game.", show_alert=True)
            except Exception:
                pass
            await send_fallback_game_link(query, chat_data)
        except Exception as e:
            logger.exception("Error in start_ai_story: %s", e)
            try:
                await query.answer("אירעה שגיאה. נסה שוב או /end_game ואז /start_game.", show_alert=True)
            except Exception:
                pass
            await send_fallback_game_link(query, chat_data)

    elif query.data == "ignore_welcome":
        await query.answer()
        await query.edit_message_text("אולי פעם אחרת! המשך יום נעים. 😊")


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    if not is_game_active(chat_data):
        await update.message.reply_text("אין משחק פעיל כרגע שאפשר לסיים! 😊")
        return
    end_game_chat(chat_data)
    await update.message.reply_text(
        "🏆 **המשחק הסתיים!**\n"
        "מקווים שנהניתם. עכשיו אפשר להתחיל הרפתקה חדשה עם פקודת /start_game."
    )


def register_game_handlers(application) -> None:
    application.add_handler(CommandHandler("start_game", start_game))
    application.add_handler(CommandHandler("end_game", end_game))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_any_message))
