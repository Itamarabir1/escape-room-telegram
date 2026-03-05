# pyright: reportMissingImports=false
"""Application configuration. Single source for env and derived values."""
import os
from pathlib import Path
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)


def _str_env(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip().rstrip("/")


def _ensure_db_ssl(url: str) -> str:
    if not url or "sslmode=" in url or "ssl=" in url.lower():
        return url
    if os.getenv("RENDER") or os.getenv("ENV", "production") == "production":
        sep = "&" if "?" in url else "?"
        return url + sep + "sslmode=require"
    return url


class Config:
    # --- Telegram ---
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_BOT_USERNAME = _str_env("TELEGRAM_BOT_USERNAME", "").lstrip("@")
    TELEGRAM_MINI_APP_SHORT_NAME = _str_env("TELEGRAM_MINI_APP_SHORT_NAME", "").strip("/")

    # --- URLs (API, web app / frontend) ---
    API_BASE_URL = _str_env("API_BASE_URL")
    WEBAPP_URL = _str_env("WEBAPP_URL")
    FRONTEND_ORIGIN_FALLBACK = _str_env("FRONTEND_ORIGIN_FALLBACK") or "http://localhost:5173"
    VITE_API_URL = _str_env("VITE_API_URL")

    # --- App ---
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

    # --- Redis ---
    REDIS_URL: str = (
        os.getenv("REDIS_URL")
        or os.getenv("REDIS_INTERNAL_URL")
        or "redis://localhost:6379/0"
    )

    # --- Database ---
    _raw_db_url: str = os.getenv(
        "DATABASE_URL",
        os.getenv("POSTGRES_URL", "postgresql://escape_user:escape_pass@postgres:5432/escape_room"),
    )
    DATABASE_URL: str = _ensure_db_ssl(_raw_db_url)
    GAME_SESSION_TTL: int = int(os.getenv("GAME_SESSION_TTL", "86400"))

    @staticmethod
    def base_url() -> str:
        """Base URL of the web app (frontend), not the API. Used for building game links."""
        return Config.WEBAPP_URL or "http://localhost:8000"

    @staticmethod
    def get_cors_origins() -> list[str]:
        """CORS allowed origins: web app URL, fallback, and local dev origins."""
        origins = [
            Config.WEBAPP_URL or Config.FRONTEND_ORIGIN_FALLBACK,
            Config.FRONTEND_ORIGIN_FALLBACK,
            "http://localhost:3000",
            "http://localhost:5173",
        ]
        return list(dict.fromkeys(o for o in origins if o))


def log_config_warnings() -> None:
    """Log config warnings. Call once at startup (e.g. from main bootstrap)."""
    if _env_path.exists():
        logger.info("Loaded environment from %s", _env_path)
    else:
        logger.warning(".env file not found at %s, using system env vars", _env_path)
    if not Config.TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_TOKEN is missing")
    else:
        logger.info("TELEGRAM_TOKEN is set (length=%d)", len(Config.TELEGRAM_TOKEN))
    if not Config.TELEGRAM_BOT_USERNAME or not Config.TELEGRAM_MINI_APP_SHORT_NAME:
        logger.warning(
            "Mini App deep-link config missing: set TELEGRAM_BOT_USERNAME and TELEGRAM_MINI_APP_SHORT_NAME. "
            "Fallback URL /game?game_id=... will be used."
        )


config = Config()

# Project paths (media, audio, room assets)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
IMAGES_DIR = _REPO_ROOT / "images"
ROOM_ASSETS_DIR = _BACKEND_DIR / "room_assets"
AUDIO_DIR = _BACKEND_DIR / "audio"
LORE_WAV_PATH = AUDIO_DIR / "lore.wav"
