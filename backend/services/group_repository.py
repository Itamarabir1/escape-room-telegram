# pyright: reportMissingImports=false
"""Persist Telegram group names and leaderboard (Groups table)."""
import logging
from datetime import datetime, timezone
from typing import Any

from db.models import Group
from db.session import get_session

logger = logging.getLogger(__name__)


def upsert_group(chat_id: int, group_name: str | None = None, started_at: datetime | None = None) -> None:
    """
    Insert or update a group. group_id = chat_id (Telegram chat).
    If started_at is given, sets it; otherwise leaves existing.
    """
    now = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            row = session.query(Group).filter(Group.group_id == chat_id).first()
            if row:
                if group_name is not None:
                    row.group_name = group_name[:100] if group_name else None
                if started_at is not None:
                    row.started_at = started_at
                logger.debug("Updated group chat_id=%s name=%s", chat_id, group_name)
            else:
                session.add(
                    Group(
                        group_id=chat_id,
                        group_name=group_name[:100] if group_name else None,
                        started_at=started_at or now,
                        created_at=now,
                    )
                )
                logger.info("Created group in DB: chat_id=%s name=%s", chat_id, group_name)
    except Exception as e:
        logger.warning("Failed to upsert group in DB: %s", e, exc_info=True)


def set_finished_at(chat_id: int, finished_at: datetime | None = None) -> None:
    """Set finished_at for a group (when game ends)."""
    when = finished_at or datetime.now(timezone.utc)
    try:
        with get_session() as session:
            row = session.query(Group).filter(Group.group_id == chat_id).first()
            if row:
                row.finished_at = when
                logger.debug("Set finished_at for group chat_id=%s", chat_id)
            # If group doesn't exist (e.g. no name was set), we could insert with finished_at only;
            # for simplicity we only update existing.
    except Exception as e:
        logger.warning("Failed to set finished_at in DB: %s", e, exc_info=True)


def get_top10_groups() -> list[dict[str, Any]]:
    """
    Return top 10 groups that have finished, ordered by fastest completion (shortest duration).
    Each dict: group_name, duration_seconds, finished_at.
    """
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
