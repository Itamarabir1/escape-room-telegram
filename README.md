# Telegram Bot – חדר בריחה

בוט טלגרם עם Web App (FastAPI) לחדר בריחה.

## התקנה מקומית

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

3. הרצת השרת (מתוך תיקיית `backend`):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
   או: `python -m app.main` (מתוך `backend`).

4. הגדר ב-`.env` את `WEBAPP_URL` לכתובת שבה השרת רץ (למשל `http://localhost:8000`) כדי שה-Web App יעבוד.

## פריסה ל-Render

1. העלה את הפרויקט ל-GitHub.
2. ב-[Render](https://render.com): **New → Blueprint**.
3. חבר את ה-repository (או בחר "From existing render.yaml" אם יש כבר `render.yaml`).
4. Render יקרא את `render.yaml` שבשורש הפרויקט. אשר את השירות ולחץ **Deploy Blueprint**.
5. ב-**Environment** של השירות הוסף:
   - `TELEGRAM_TOKEN` – הטוקן מ-@BotFather.
   - `WEBAPP_URL` – כתובת השירות ב-Render (למשל `https://telegram-bot-xxxx.onrender.com`), **בלי** סלאש בסוף.
6. אחרי הפריסה, עדכן ב-@BotFather את ה-Web App URL ל־`https://<שירות-שלך>.onrender.com/game` אם נדרש.

### בדיקת חיים

- `GET /health` – מחזיר `{"status":"ok"}` (משמש את Render לבדיקת חיים).

## מבנה הפרויקט

- `backend/app/main.py` — FastAPI + הבוט (נקודת כניסה)
- `backend/app/static/` — דף ה-Web App (HTML)
- `backend/config.py` — הגדרות (טוקן, WEBAPP_URL)
- `backend/game_manager.py`, `backend/game_logic.py` — לוגיקת משחק
- `frontend/` — גרסת ה-HTML לפרונט (משוכפלת ל-`backend/app/static` לפריסה)
- `render.yaml` — הגדרת Blueprint ל-Render
