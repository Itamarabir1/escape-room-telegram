# pyright: reportMissingImports=false
"""Build Telegram Application and run webhook or polling."""
import logging
import os

from telegram.error import NetworkError
from telegram.ext import ApplicationBuilder

from config.config import config
from api.bot.handlers.start import register_start_handler
from api.bot.handlers.game import register_game_handlers

logger = logging.getLogger(__name__)


def create_telegram_app():
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    register_start_handler(application)
    register_game_handlers(application)
    return application


async def run_telegram(application) -> None:
    await application.initialize()
    await application.start()

    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared (drop_pending_updates=True)")

    if os.getenv("RENDER") and config.VITE_API_URL:
        base = config.VITE_API_URL.rstrip("/")
        webhook_url = f"{base}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        logger.info("Webhook set: %s (RENDER=1, polling disabled)", webhook_url)
    else:
        try:
            await application.updater.start_polling()
            logger.info("Polling started (local)")
        except NetworkError as e:
            logger.warning(
                "Polling failed (cannot reach Telegram): %s. On Render set RENDER and VITE_API_URL for webhook.",
                e,
            )
