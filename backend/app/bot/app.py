# pyright: reportMissingImports=false
"""Build Telegram Application and run webhook or polling."""
import logging

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
    """Initialize, start, and set webhook (production) or polling (local)."""
    await application.initialize()
    await application.start()
    # Webhook must point to THIS backend (BACKEND_PUBLIC_URL), not the frontend (WEBAPP_URL)
    webhook_base = config.BACKEND_PUBLIC_URL or config.WEBAPP_URL
    if webhook_base:
        webhook_url = f"{webhook_base}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        logger.info("Webhook set: %s", webhook_url)
    else:
        try:
            await application.updater.start_polling()
            logger.info("Polling started (no WEBAPP_URL)")
        except NetworkError as e:
            logger.warning(
                "Polling failed (cannot reach Telegram): %s. Check internet/proxy. Web app and API still work.",
                e,
            )
