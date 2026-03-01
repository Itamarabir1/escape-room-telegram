# pyright: reportMissingImports=false
"""Group game: /end_game, welcome, top10. Lobby/start flow is in start_game.py."""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from services.game_session import is_game_active, end_game_chat
from repositories.group_repository import get_top10_groups, set_finished_at
from utils.urls import game_page_url

logger = logging.getLogger(__name__)


def _game_keyboard(game_id: str) -> InlineKeyboardMarkup:
    url = game_page_url(game_id)
    keyboard = [
        [InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton("🏆 עשרת הגדולים ביותר", callback_data="top10")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _game_keyboard_url_fallback(game_id: str) -> InlineKeyboardMarkup:
    url = game_page_url(game_id)
    keyboard = [
        [InlineKeyboardButton("🎮 כניסה למשחק", url=url)],
        [InlineKeyboardButton("🏆 עשרת הגדולים ביותר", callback_data="top10")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_game_button_or_link(message, game_id: str, intro: str) -> None:
    try:
        await message.reply_text(intro, reply_markup=_game_keyboard(game_id))
    except BadRequest as e:
        err_msg = getattr(e, "message", None) or str(e)
        if "button" in err_msg.lower():
            await message.reply_text(
                intro + "\n\n(לחץ על הכפתור למטה כדי להיכנס.)",
                reply_markup=_game_keyboard_url_fallback(game_id),
            )
        else:
            raise


async def send_fallback_game_link(query, chat_data: dict) -> None:
    game_id = chat_data.get("game_id")
    if not game_id:
        await query.message.reply_text("אירעה שגיאה בהתחלת המשחק. נסה /end_game ואז /start_game.")
        return
    await query.message.reply_text(
        "המשחק מוכן. לחץ על הכפתור למטה כדי להיכנס:",
        reply_markup=_game_keyboard_url_fallback(game_id),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_data = context.chat_data
    logger.debug("callback data=%s chat_id=%s", query.data, update.effective_chat.id if update.effective_chat else None)

    if query.data == "top10":
        top = get_top10_groups()
        if not top:
            await query.answer("עדיין אין תוצאות. היו הראשונים לסיים! 🏆", show_alert=True)
            return
        medals = ("🥇", "🥈", "🥉") + ("4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")
        lines = ["🏆 *עשרת הגדולים ביותר* 🏆\n"]
        for i, row in enumerate(top, 1):
            name = (row["group_name"] or "קבוצה").replace("*", "•").replace("_", "\\_")
            sec = row.get("duration_seconds") or 0
            m, s = divmod(sec, 60)
            time_str = f"{m} דק׳ {s} שניות" if m else f"{s} שניות"
            icon = medals[i - 1] if i <= len(medals) else f"{i}."
            lines.append(f"{icon} *{name}*\n   ⏱ {time_str}")
        await query.answer()
        await query.message.reply_text("\n".join(lines), parse_mode="Markdown")

    elif query.data == "ignore_welcome":
        await query.answer()
        await query.edit_message_text("אולי פעם אחרת! המשך יום נעים. 😊")


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    for new_user in update.message.new_chat_members:
        if new_user.is_bot:
            continue
        if is_game_active(chat_data):
            game_id = chat_data.get("game_id")
            if game_id:
                await send_game_button_or_link(
                    update.message,
                    game_id,
                    f"אהלן {new_user.first_name}! יש משחק פעיל בקבוצה. לחץ על הכפתור למטה כדי להצטרף:",
                )
                return
        keyboard = [
            [
                InlineKeyboardButton("כן ✅", callback_data="lobby_join"),
                InlineKeyboardButton("לא ❌", callback_data="ignore_welcome"),
            ]
        ]
        await update.message.reply_text(
            f"אהלן {new_user.first_name}! רוצה להצטרף למשחק?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    if chat_data.get("awaiting_group_name") is None:
        return
    del chat_data["awaiting_group_name"]


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    if not is_game_active(chat_data):
        await update.message.reply_text("אין משחק פעיל כרגע שאפשר לסיים! 😊")
        return
    starter_id = chat_data.get("started_by_user_id")
    user_id = update.message.from_user.id if update.message and update.message.from_user else None
    if starter_id is not None and user_id is not None and user_id != starter_id:
        await update.message.reply_text("רק מי שהתחיל את המשחק (מי שכתב /start_game) יכול לסיים אותו. ✋")
        return
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is not None:
        set_finished_at(chat_id)
    end_game_chat(chat_data)
    await update.message.reply_text(
        "🏆 **המשחק הסתיים!**\n"
        "מקווים שנהניתם. עכשיו אפשר להתחיל הרפתקה חדשה עם פקודת /start_game."
    )


def register_game_handlers(application) -> None:
    application.add_handler(CommandHandler("end_game", end_game))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_any_message))
