# pyright: reportMissingImports=false
"""Persist game registration to DB: one row per (chat, Telegram user) in Players."""
import logging
from datetime import datetime, timezone

from db.models import Player
from db.session import get_session

logger = logging.getLogger(__name__)


def register_player(chat_id: int, telegram_user_id: int, name: str) -> None:
    """
    Upsert a player for this chat. Uses (username, group_name) = (name_id, str(chat_id))
    so each Telegram user gets one row per chat. On duplicate, joined_at is updated.
    """
    username = f"{name}_{telegram_user_id}"[:50]
    group_name = str(chat_id)
    now = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            existing = (
                session.query(Player)
                .filter(Player.username == username, Player.group_name == group_name)
                .first()
            )
            if existing:
                existing.joined_at = now
                logger.debug("Updated player joined_at: %s in chat %s", name, chat_id)
            else:
                session.add(
                    Player(
                        username=username,
                        group_name=group_name,
                        joined_at=now,
                    )
                )
                logger.info("Registered player in DB: %s (chat_id=%s)", name, chat_id)
    except Exception as e:
        logger.warning("Failed to register player in DB: %s", e, exc_info=True)
