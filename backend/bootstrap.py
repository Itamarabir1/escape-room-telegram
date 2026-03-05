# pyright: reportMissingImports=false
"""Startup: config, DB, telegram app, background tasks."""
import asyncio
import logging

from fastapi import FastAPI

from config import log_config_warnings
from infrastructure.database.session import init_db, wait_for_db
from bot.app import create_telegram_app, run_telegram
from services.game_lifecycle_service import check_expired_games_loop
from services.sse_registry import sse_pubsub_listener_loop

logger = logging.getLogger(__name__)


async def bootstrap(app: FastAPI) -> None:
    log_config_warnings()
    logger.info("Startup: waiting for database")
    wait_for_db()
    logger.info("Startup: database is ready")
    init_db()
    logger.info("Startup: database init completed")
    tg_app = create_telegram_app()
    app.state.tg_app = tg_app
    asyncio.create_task(check_expired_games_loop())
    asyncio.create_task(sse_pubsub_listener_loop())
    logger.info("Startup: starting telegram runtime")
    await run_telegram(tg_app)
    logger.info("Startup: telegram runtime started")
