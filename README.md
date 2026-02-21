# Telegram Bot

בוט טלגרם (Python).

## התקנה

1. צור סביבה וירטואלית והתקן תלויות:
   ```bash
   uv sync
   ```
   או עם pip:
   ```bash
   pip install -e .
   ```

2. העתק את קובץ הדוגמה והגדר טוקן:
   ```bash
   cp backend/.env.example backend/.env
   ```
   ערוך את `backend/.env` והכנס את הטוקן מ-@BotFather.

3. הרצה:
   ```bash
   python main.py
   ```

## מבנה הפרויקט

- `main.py` — נקודת הכניסה
- `backend/` — לוגיקת הבוט והמשחק
- `frontend/` — קבצי ווב (אם רלוונטי)
