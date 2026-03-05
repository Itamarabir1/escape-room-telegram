# pyright: reportMissingImports=false
"""Build Telegram Application and run webhook or polling."""
import logging
import os

from telegram.error import NetworkError
from telegram.ext import ApplicationBuilder, ContextTypes

from config.config import config
from api.bot.handlers.start import register_start_handler
from api.bot.handlers.start_game import register_start_game_handler
from api.bot.handlers.game import register_game_handlers

logger = logging.getLogger(__name__)


async def _telegram_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log unhandled telegram handler exceptions with update context."""
    if context.error is None:
        return
    logger.exception("Telegram handler error. update=%s error=%s", update, context.error)


def create_telegram_app():
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    application.add_error_handler(_telegram_error_handler)
    register_start_handler(application)
    register_start_game_handler(application)
    register_game_handlers(application)
    return application


async def run_telegram(application) -> None:
    await application.initialize()
    await application.start()

    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared (drop_pending_updates=True)")

    if os.getenv("RENDER") and config.API_BASE_URL:
        base = config.API_BASE_URL.rstrip("/")
        webhook_url = f"{base}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        logger.info("Telegram mode=webhook webhook_url=%s", webhook_url)
    else:
        if application.updater is None:
            raise RuntimeError("Telegram updater is unavailable; cannot start polling")
        try:
            await application.updater.start_polling()
            logger.info("Telegram mode=polling status=started")
        except NetworkError as e:
            logger.exception("Telegram mode=polling status=failed err=%s", e)
            raise RuntimeError(
                "Polling failed (cannot reach Telegram). Configure webhook on hosted environments."
            ) from e
