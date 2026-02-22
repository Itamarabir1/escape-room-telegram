# Telegram Bot – חדר בריחה

בוט טלגרם עם Web App (FastAPI) לחדר בריחה.

## פיתוח מקומי

כדי שהכל ירוץ אצלך בלי Render (טעינה מהירה, ללא המתנה ל-deploy):

1. **התקנת תלויות** (פעם אחת):
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **הגדרת סביבה** – העתק והגדר טוקן:
   ```bash
   cp backend/.env.example backend/.env
   ```
   ערוך `backend/.env`: הכנס `TELEGRAM_TOKEN` מ-@BotFather.  
   **אל תגדיר** `WEBAPP_URL` (השאר ריק או ללא השורה) – אז הבוט ישתמש ב-polling והלינקים יופנו ל-`http://localhost:8000`.

3. **בניית הפרונט** (פעם אחת או אחרי שינויים בפרונט):
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   הבקאנד מגיש את הקבצים מ-`frontend/dist` ב-`/static` ו-`/game`.

4. **הרצת השרת** (תמיד מתוך `backend`):
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   או: `uvicorn app.main:app --reload --port 8000`

5. **בדיקה**: פתח את הבוט בקבוצה → `/start_game` → הירשם → "כולם פה, אפשר להתחיל!" → הבוט ישלח לינק. פתח את הלינק **בדפדפן במחשב** (`http://localhost:8000/game?game_id=...`) – הדף וה-API רצים מהמחשב שלך.

   **פיתוח פרונט**: להריץ במקביל `cd frontend && npm run dev` — אז לגלוש ל-`http://localhost:5173/game?game_id=...` (Vite עם proxy ל-API).  
   (מהטלפון הלינק localhost לא יעבוד – לבדוק מהמחשב או אחרי deploy ל-Render.)

**סיכום מקומי:** רק `TELEGRAM_TOKEN` ב-`.env`, בלי `WEBAPP_URL`. אותו קוד – ב-Render תגדיר `WEBAPP_URL` ב-Dashboard.

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

- `GET /health` – קובץ ייעודי: `app/routes/health.py`. מחזיר `{"status": "awake", "mode": "production"}` (לסקריפטים חיצוניים ו-Render). `mode` מתוך `ENV` (ברירת מחדל: production).

## מבנה הפרויקט (הפרדה backend / frontend)

- **`backend/`** — קוד Python בלבד (FastAPI, API, בוט). בפרודקשן מגיש **רק** את תוצאת הבנייה מ-`frontend/dist` ב-`/static` ו-`/game` (ללא קבצי מקור פרונט).
- **`frontend/`** — פרויקט Vite + React + TypeScript. מקור ב-`src/`; אחרי `npm run build` נוצר `dist/`. הפרונט מדבר עם הבקאנד רק דרך HTTP.

ראה **`frontend/README.md`** לסקריפטים והרצת פיתוח.

## Backend – Layered Architecture

- **`backend/ARCHITECTURE.md`** — סכמה (Mermaid) והסבר על השכבות
- **Presentation** (`app/`): `main.py` (חיבור בלבד), `api/`, `routes/` (כולל **`routes/health.py`** – health ייעודי), `bot/`. ה-Web App מגיש מתוך **`frontend/dist`** (תוצאת `npm run build`).
- **Application** (`services/`): `game_session.py` — לוגיקת משחק
- **Domain** (`domain/`): `game.py` — סכמה (`GameStateResponse`, `HealthResponse`)
- **Infrastructure**: `config.py` (כולל `MODE`), `utils/urls.py`
- `render.yaml` — הגדרת Blueprint ל-Render
