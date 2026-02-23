# pyright: reportMissingImports=false
"""Application configuration. Single source for env and derived values (e.g. BASE_URL)."""
import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    PORT = int(os.getenv("PORT", "8000"))
    MODE = os.getenv("ENV", "production")  # production | development (for health, reload)


    PROJECT_NAME: str = "AI Escape Room"
    
    # AI Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # v1beta supports 2.x; gemini-1.5-flash is not available in new API
    GEMINI_IMAGE_MODEL: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")  # image generation (Gemini Imagen / "ננו באננה")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_FLUX_MODEL: str = os.getenv("HF_FLUX_MODEL", "black-forest-labs/FLUX.1-schnell")  # or FLUX.1-dev for higher quality (slower)
    ELEVEN_API_KEY: str = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY", "")

    # AWS Settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "")

    # Redis – live game session (room, items, puzzles). Used when REDIS_URL is set.
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Database – PostgreSQL only (schema in db/schema.sql)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        os.getenv("POSTGRES_URL", "postgresql://escape_user:escape_pass@localhost:5432/escape_room"),
    )

    # Redis TTL for game session (seconds). Default 24h.
    GAME_SESSION_TTL: int = int(os.getenv("GAME_SESSION_TTL", "86400"))

    @staticmethod
    def base_url() -> str:
        """Base URL of this app (Web App + API). Local dev: localhost; production: WEBAPP_URL."""
        return Config.WEBAPP_URL or "http://localhost:8000"

    if not TELEGRAM_TOKEN:
        raise ValueError(
            "❌ TELEGRAM_TOKEN חסר. הגדר בקובץ backend/.env או במשתני הסביבה (ב-Render: Environment)."
        )


config = Config()