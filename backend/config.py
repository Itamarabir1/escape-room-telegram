# pyright: reportMissingImports=false
import os
from pathlib import Path
from dotenv import load_dotenv

# טוען .env מתוך תיקיית backend (עובד גם כשמריצים מתוך שורש הפרויקט)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")  # כתובת השרת ב-Render (ללא / בסוף)
    PORT = int(os.getenv("PORT", "8000"))

    if not TELEGRAM_TOKEN:
        raise ValueError(
            "❌ TELEGRAM_TOKEN חסר. הגדר בקובץ backend/.env או במשתני הסביבה (ב-Render: Environment)."
        )