# pyright: reportMissingImports=false
"""Group game: /start_game, join, מתחילים, /end_game. Thin layer over game_session."""
import logging
from datetime import datetime, timezone

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
from repositories.player_repository import register_player as register_player_db
from repositories.group_repository import upsert_group, get_top10_groups, set_finished_at
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


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    starter_id = update.message.from_user.id if update.message and update.message.from_user else None
    if starter_id is not None:
        chat_data["started_by_user_id"] = starter_id
    if is_game_active(chat_data):
        game_id = chat_data.get("game_id")
        if game_id and get_game_by_id(game_id) is None:
            end_game_chat(chat_data)
            if starter_id is not None:
                chat_data["started_by_user_id"] = starter_id
        else:
            await update.message.reply_text("המשחק כבר התחיל! אי אפשר להירשם שוב כרגע. ✋")
            return
    start_registration(chat_data)
    keyboard = [
        [InlineKeyboardButton("אני רוצה לשחק! 🙋‍♂️", callback_data="join_game")],
        [InlineKeyboardButton("🏆 עשרת הגדולים ביותר", callback_data="top10")],
    ]
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
        chat = update.effective_chat
        chat_id = chat.id if chat else 0
        group_name = (chat.title or "קבוצה").strip() if chat else "קבוצה"
        if not group_name:
            group_name = "קבוצה"
        now = datetime.now(timezone.utc)
        upsert_group(chat_id, group_name=group_name[:100], started_at=now)
        try:
            game_id = finish_registration(chat_id, chat_data)
            await query.answer()
            safe_name = group_name.replace("*", "•").replace("_", "\\_")[:80]
            await query.message.reply_text(
                f"✅ **{safe_name}** – ההרשמה נסגרה!\n\nלחץ על הכפתור למטה כדי להיכנס למשחק.",
                reply_markup=_game_keyboard(game_id),
                parse_mode="Markdown",
            )
        except BadRequest as e:
            err_msg = getattr(e, "message", None) or str(e)
            if "button" in err_msg.lower():
                game_id = chat_data.get("game_id", "")
                await query.answer()
                await query.message.reply_text(
                    "✅ ההרשמה נסגרה! לחץ על הכפתור למטה כדי להיכנס למשחק:",
                    reply_markup=_game_keyboard_url_fallback(game_id),
                )
            else:
                await query.answer()
                raise
        return

    elif query.data == "top10":
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
                InlineKeyboardButton("כן ✅", callback_data="join_game"),
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
    application.add_handler(CommandHandler("start_game", start_game))
    application.add_handler(CommandHandler("end_game", end_game))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_any_message))
