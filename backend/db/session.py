# pyright: reportMissingImports=false
"""SQLAlchemy engine and session factory. Use get_session() or dependency injection."""
import logging
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import config
from db.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # set True for SQL logging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def wait_for_db(max_attempts: int = 30, interval: float = 2.0) -> None:
    """Wait for the database to accept connections (e.g. after Render starts DB and web together)."""
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection OK")
            return
        except Exception as e:
            if attempt == max_attempts:
                raise
            logger.warning("Database not ready (attempt %s/%s): %s", attempt, max_attempts, e)
            time.sleep(interval)


def init_db() -> None:
    """Create all tables. Call after DB is up (e.g. on app startup or migration)."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for a DB session. Use: with get_session() as session: ..."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
