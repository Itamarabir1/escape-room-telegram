# pyright: reportMissingImports=false
"""Build Telegram Application and run webhook or polling."""
import logging
import os

from telegram.error import NetworkError
from telegram.ext import ApplicationBuilder

from config import config
from app.bot.handlers.start import register_start_handler
from app.bot.handlers.game import register_game_handlers

logger = logging.getLogger(__name__)


def create_telegram_app():
    """Build Application with token and register all handlers."""
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    register_start_handler(application)
    register_game_handlers(application)
    return application


async def run_telegram(application) -> None:
    """Initialize and either set webhook (Render) or start polling (local).
    Always clear any existing webhook first to avoid 'getUpdates while webhook is active' conflict."""
    await application.initialize()
    await application.start()

    # Clear any old webhook before setting a new one or starting polling
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
