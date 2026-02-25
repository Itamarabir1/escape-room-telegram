# pyright: reportMissingImports=false
"""Application configuration. Single source for env and derived values (e.g. BASE_URL)."""
import os
from pathlib import Path
import logging

from dotenv import load_dotenv

# הגדרת לוגר כדי שנדע אם ה-.env נטען
logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)
    logger.info(f"Loaded environment from {_env_path}")
else:
    logger.warning(f".env file not found at {_env_path}, using system env vars")


class Config:
    # --- תשתית ---
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    PORT = int(os.getenv("PORT", "8000"))
    MODE = os.getenv("ENV", "production")  # production | development

    PROJECT_NAME: str = "AI Escape Room"
    
    # --- AI Keys (תיקון שמות משתנים) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # עדכון לגרסה יציבה
    GEMINI_IMAGE_MODEL: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.0-flash") 
    
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_FLUX_MODEL: str = os.getenv("HF_FLUX_MODEL", "black-forest-labs/FLUX.1-schnell")

    # --- AWS ---
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "")

    # Redis: ב-Docker Compose מוגדר REDIS_URL=redis://redis:6379/0 ב-compose.
    # ב-Render: REDIS_INTERNAL_URL או REDIS_URL מ-Redis addon. ברירת מחדל ל-localhost (מקומי בלי Docker).
    REDIS_URL: str = (
        os.getenv("REDIS_URL")
        or os.getenv("REDIS_INTERNAL_URL")
        or "redis://localhost:6379/0"
    )

    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        os.getenv("POSTGRES_URL", "postgresql://escape_user:escape_pass@postgres:5432/escape_room")
    )

    GAME_SESSION_TTL: int = int(os.getenv("GAME_SESSION_TTL", "86400"))

    @staticmethod
    def base_url() -> str:
        return Config.WEBAPP_URL or "http://localhost:8000"

# בדיקת תקינות מינימלית
if not Config.TELEGRAM_TOKEN:
    print("❌ WARNING: TELEGRAM_TOKEN is missing!")

config = Config()