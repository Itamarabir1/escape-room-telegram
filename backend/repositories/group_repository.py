# pyright: reportMissingImports=false
"""Persist Telegram group names and leaderboard (Groups table)."""
import logging
from datetime import datetime, timezone
from typing import Any

from models.db_models import Group
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


def get_top10_groups() -> list[dict[str, Any]]:
    try:
        with get_session() as session:
            rows = (
                session.query(Group)
                .filter(Group.finished_at.isnot(None), Group.started_at.isnot(None))
                .all()
            )
            result = []
            for g in rows:
                if not g.started_at or not g.finished_at:
                    continue
                delta = g.finished_at - g.started_at
                duration = int(delta.total_seconds())
                result.append({
                    "group_name": g.group_name or f"קבוצה {g.group_id}",
                    "duration_seconds": duration,
                    "finished_at": g.finished_at,
                })
            result.sort(key=lambda x: x["duration_seconds"])
            return result[:10]
    except Exception as e:
        logger.warning("Failed to get top10 groups: %s", e, exc_info=True)
        return []
