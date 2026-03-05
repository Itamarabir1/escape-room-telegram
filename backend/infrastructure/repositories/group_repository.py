# pyright: reportMissingImports=false
"""Persist Telegram group finished_at (Groups table). Leaderboard uses Redis (redis_get_leaderboard_top10)."""
import logging
from datetime import datetime, timezone

from infrastructure.models.db_models import Group
from infrastructure.database.session import get_session

logger = logging.getLogger(__name__)


def set_finished_at(chat_id: int, finished_at: datetime | None = None) -> None:
    when = finished_at or datetime.now(timezone.utc)
    try:
        with get_session() as session:
            row = session.query(Group).filter(Group.group_id == chat_id).first()
            if row:
                row.finished_at = when
                logger.debug("Set finished_at for group chat_id=%s", chat_id)
    except Exception as e:
        logger.warning("Failed to set finished_at in DB: %s", e, exc_info=True)
