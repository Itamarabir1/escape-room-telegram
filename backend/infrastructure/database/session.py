# pyright: reportMissingImports=false
"""SQLAlchemy engine and session factory. Use get_session() or dependency injection."""
import logging
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.config import config
from models.db_models import Base

logger = logging.getLogger(__name__)
DATABASE_URL = config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=60,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def wait_for_db(max_attempts: int = 30, interval: float = 2.0) -> None:
    if max_attempts < 1:
        return
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection OK (attempt %d)", attempt)
            return
        except Exception as e:
            logger.warning("Database not ready (attempt %d/%d): %s", attempt, max_attempts, e)
            if attempt == max_attempts:
                raise
            time.sleep(interval)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
