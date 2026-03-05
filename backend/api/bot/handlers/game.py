# pyright: reportMissingImports=false
"""Group game: /end_game, welcome, top10. Lobby/start flow is in start_game.py."""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from services.game_session import is_game_active, end_game_chat
from repositories.group_repository import set_finished_at
from infrastructure.redis.redis_client import redis_get_leaderboard_top10
from utils.urls import game_entry_url

logger = logging.getLogger(__name__)


def _game_keyboard(game_id: str) -> InlineKeyboardMarkup:
    url = game_entry_url(game_id)
    keyboard = [
        [InlineKeyboardButton("🎮 כנס למשחק", url=url)],
        [InlineKeyboardButton("🏆 עשרת הגדולים ביותר", callback_data="top10")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_game_button_or_link(message, game_id: str, intro: str) -> None:
    await message.reply_text(intro, reply_markup=_game_keyboard(game_id))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logger.debug("callback data=%s chat_id=%s", query.data, update.effective_chat.id if update.effective_chat else None)

    if query.data == "top10":
        await query.answer()
        top = redis_get_leaderboard_top10()
        if not top:
            await query.message.reply_text("עדיין אין תוצאות. היו הראשונים לסיים! 🏆")
            return
        medals = ("🥇", "🥈", "🥉") + ("4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")
        lines = ["🏆 *עשרת הגדולים ביותר* 🏆\n"]
        for i, (member, score) in enumerate(top, 1):
            name = (member if member.isdigit() is False else f"קבוצה {member}").replace("*", "•").replace("_", "\\_")
            sec = int(score)
            m, s = divmod(sec, 60)
            time_str = f"{m} דק׳ {s} שניות" if m else f"{s} שניות"
            icon = medals[i - 1] if i <= len(medals) else f"{i}."
            lines.append(f"{icon} *{name}*\n   ⏱ {time_str}")
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
