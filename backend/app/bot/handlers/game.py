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
from services.group_repository import upsert_group, get_top10_groups, set_finished_at
from utils.urls import game_page_url
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# --- Helpers: send game link as button or plain text ---


def _game_keyboard(game_id: str) -> InlineKeyboardMarkup:
    """Web App button + Top 10 leaderboard button."""
    url = game_page_url(game_id)
    keyboard = [
        [InlineKeyboardButton("🎮 שחק עכשיו!", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton("🏆 10 הטובים ביותר", callback_data="top10")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_game_button_or_link(message, game_id: str, intro: str) -> None:
    """Sends Web App button and Top 10 button; on Button_type_invalid falls back to plain link."""
    url = game_page_url(game_id)
    keyboard = _game_keyboard(game_id)
    try:
        await message.reply_text(intro, reply_markup=keyboard)
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
        # Ask only the user who clicked for the group name, then we'll finish registration
        chat_id = update.effective_chat.id if update.effective_chat else 0
        chat_data["awaiting_group_name"] = user.id
        await query.answer()
        name = user.first_name or "חבר/ה בקבוצה"
        await query.message.reply_text(
            f"👋 {name}, מה השם של הקבוצה? כתוב כאן בקבוצה (רק אתה צריך לענות)."
        )
        return

    elif query.data == "top10":
        top = get_top10_groups()
        if not top:
            await query.answer("עדיין אין תוצאות. היו הראשונים לסיים! 🏆", show_alert=True)
            return
        lines = ["🏆 **10 הטובים ביותר**\n"]
        for i, row in enumerate(top, 1):
            name = (row["group_name"] or "קבוצה").replace("*", "•")
            sec = row.get("duration_seconds") or 0
            m, s = divmod(sec, 60)
            time_str = f"{m} דק׳ {s} שניות" if m else f"{s} שניות"
            lines.append(f"{i}. **{name}** — {time_str}")
        await query.answer()
        await query.message.reply_text("\n".join(lines), parse_mode="Markdown")

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
    """Handle group name reply after 'כולם פה' – only the user who clicked should answer."""
    chat_data = context.chat_data
    awaiting = chat_data.get("awaiting_group_name")
    if awaiting is None:
        return
    user = update.message.from_user
    if not user or user.id != awaiting:
        return
    group_name = (update.message.text or "").strip()
    if not group_name:
        await update.message.reply_text("נא לכתוב שם קבוצה (טקסט קצר).")
        return
    chat_id = update.effective_chat.id if update.effective_chat else 0
    del chat_data["awaiting_group_name"]
    now = datetime.now(timezone.utc)
    upsert_group(chat_id, group_name=group_name, started_at=now)
    try:
        game_id = finish_registration(chat_id, chat_data)
        safe_name = group_name.replace("*", "•").replace("_", "\\_")[:80]
        await update.message.reply_text(
            f"✅ שם הקבוצה נשמר: **{safe_name}**\n\n"
            "🎲 ההרשמה נסגרה! לחץ על הכפתור \"שחק עכשיו\" למטה – ייפתח דף המשחק בדפדפן.",
            reply_markup=_game_keyboard(game_id),
            parse_mode="Markdown",
        )
    except BadRequest as e:
        err_msg = getattr(e, "message", None) or str(e)
        if "button" in err_msg.lower():
            await update.message.reply_text(
                f"שם הקבוצה נשמר. פתח את המשחק: {game_page_url(chat_data.get('game_id', ''))}"
            )
        else:
            raise


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = context.chat_data
    if not is_game_active(chat_data):
        await update.message.reply_text("אין משחק פעיל כרגע שאפשר לסיים! 😊")
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
