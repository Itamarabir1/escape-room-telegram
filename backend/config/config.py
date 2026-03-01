# pyright: reportMissingImports=false
"""Application configuration. Single source for env and derived values (e.g. BASE_URL)."""
import os
from pathlib import Path
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)
    logger.info(f"Loaded environment from {_env_path}")
else:
    logger.warning(f".env file not found at {_env_path}, using system env vars")


class Config:
    # --- Core ---
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    FRONTEND_ORIGIN_FALLBACK = (os.getenv("FRONTEND_ORIGIN_FALLBACK") or "https://escape-room-telegram.onrender.com").strip().rstrip("/")
    VITE_API_URL = (os.getenv("VITE_API_URL") or "").strip().rstrip("/")
    PORT = int(os.getenv("PORT", "8000"))
    MODE = os.getenv("ENV", "production")

    PROJECT_NAME: str = "AI Escape Room"

    # --- AI ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_IMAGE_MODEL: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.0-flash")

    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_FLUX_MODEL: str = os.getenv("HF_FLUX_MODEL", "black-forest-labs/FLUX.1-schnell")

    # --- AWS (optional) ---
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")

    REDIS_URL: str = (
        os.getenv("REDIS_URL")
        or os.getenv("REDIS_INTERNAL_URL")
        or "redis://localhost:6379/0"
    )

    # --- Database ---
    @classmethod
    def _ensure_db_ssl(cls, url: str) -> str:
        if not url or "sslmode=" in url or "ssl=" in url.lower():
            return url
        if os.getenv("RENDER") or cls.MODE == "production":
            sep = "&" if "?" in url else "?"
            return url + sep + "sslmode=require"
        return url

    _raw_db_url: str = os.getenv(
        "DATABASE_URL",
        os.getenv("POSTGRES_URL", "postgresql://escape_user:escape_pass@postgres:5432/escape_room"),
    )
    DATABASE_URL: str = ""

    GAME_SESSION_TTL: int = int(os.getenv("GAME_SESSION_TTL", "86400"))

    @staticmethod
    def base_url() -> str:
        return Config.WEBAPP_URL or "http://localhost:8000"


Config.DATABASE_URL = Config._ensure_db_ssl(Config._raw_db_url)
if not Config.TELEGRAM_TOKEN:
    logger.warning("TELEGRAM_TOKEN is missing")

config = Config()
