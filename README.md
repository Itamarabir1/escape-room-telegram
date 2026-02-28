# Telegram Bot – חדר בריחה

בוט טלגרם עם Web App (FastAPI) לחדר בריחה.

מבנה הפרויקט (Backend + Frontend): **`backend/ARCHITECTURE.md`**. חוזה API: **`backend/docs/API_CONTRACT.md`**.

## Docker (פיתוח מקומי – מומלץ)

הפרויקט כולל `docker-compose.yml` עם backend, frontend (nginx), postgres ו-redis.

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000 (האפליקציה רצה על nginx)
- **Backend API:** http://localhost:8000  
הפרונט משתמש ב-`VITE_API_URL=http://localhost:8000` (מוגדר כ-build-arg ב-compose).

להרצת רק הבקאנד + DB בלי Docker, ראה "פיתוח מקומי" למטה.

## פיתוח מקומי (בלי Docker)

כדי שהכל ירוץ אצלך בלי Render (טעינה מהירה, ללא המתנה ל-deploy):

1. **התקנת תלויות** (פעם אחת):
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **הגדרת סביבה (בקאנד)** – העתק `backend/.env.example` ל-`backend/.env` והשלם ערכים (חובה: `TELEGRAM_TOKEN` מ-@BotFather).  
   **אל תגדיר** `WEBAPP_URL` (השאר ריק) – אז הבוט ישתמש ב-polling והלינקים יופנו ל-`http://localhost:8000`.

3. **בניית הפרונט** (פעם אחת או אחרי שינויים בפרונט):
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   אם אתה רץ **בלי Docker**, הרץ את הפרונט: `npm run dev` (פורט 5173). ב-dev נטען אוטומטית `frontend/.env.development` (ב-Git) עם `VITE_API_URL=http://localhost:8000`. ל-production/build העתק `frontend/.env.example` ל-`frontend/.env` או הגדר משתנים ב-build.

4. **הרצת השרת** (תמיד מתוך `backend`):
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   או: `uvicorn app.main:app --reload --port 8000`

5. **בדיקה**: פתח את הבוט בקבוצה → `/start_game` → הירשם → "כולם פה, אפשר להתחיל!" → הבוט ישלח לינק. פתח את הלינק **בדפדפן במחשב** – אם רצת עם Docker השתמש ב-`http://localhost:3000/game?game_id=...`, אם עם uvicorn + פרונט dev השתמש ב-`http://localhost:5173/game?game_id=...` (Vite עם proxy ל-API).

**סיכום מקומי:** רק `TELEGRAM_TOKEN` ב-`.env`, בלי `WEBAPP_URL`. אותו קוד – ב-Render תגדיר `WEBAPP_URL` ב-Dashboard.

## פריסה ל-Render

1. העלה את הפרויקט ל-GitHub (אם עדיין לא).
2. ב-[Render](https://render.com): **New → Blueprint** וחבר את ה-repository.
3. `render.yaml` מגדיר:
   - **escape-room-telegram-api** – backend (Docker: `backend/Dockerfile`). לא מגיש קבצי פרונט.
   - **escape-room-telegram** – frontend (Docker: `frontend/Dockerfile`, nginx).
   - Postgres + Redis (keyvalue).
4. ב-**Environment** של כל שירות:
   - **Backend (escape-room-telegram-api):** `TELEGRAM_TOKEN`, `WEBAPP_URL` = כתובת הפרונט (`https://escape-room-telegram.onrender.com`), ושאר ה-secrets מ-`escape-room-secrets`.
   - **Frontend (escape-room-telegram):** `VITE_API_URL` = כתובת הבקאנד (`https://escape-room-telegram-api.onrender.com`), `VITE_BASE_PATH` = `/` (לבנייה ל-root).
5. אחרי הפריסה, עדכן ב-@BotFather את ה-Web App URL לכתובת **הפרונט** (`https://escape-room-telegram.onrender.com/game`).

**אין צורך יותר** לבנות `frontend/dist` locally ולהעלות ל-Git – הפרונט נבנה על Render מתוך `frontend/Dockerfile`.

### בדיקת חיים

- `GET /health` – קובץ ייעודי: `app/routes/health.py`. מחזיר `{"status": "awake", "mode": "production"}` (לסקריפטים חיצוניים ו-Render). `mode` מתוך `ENV` (ברירת מחדל: production).

## מבנה הפרויקט (הפרדה backend / frontend)

- **`backend/`** — קוד Python (FastAPI, API, בוט). בפרודקשן **לא** מגיש קבצי פרונט; `/game` מפנה ל-`WEBAPP_URL`.
- **`frontend/`** — Vite + React + TypeScript. נבנה ל-Docker (node build + nginx) או ל-`dist/` בפיתוח. משתמש ב-`VITE_API_URL` (ברירת מחדל בקוד: `http://localhost:8000`). תבנית: `frontend/.env.example`; פיתוח: `frontend/.env.development` (נטען ב-`npm run dev`).

## ניקוי – קבצים שאפשר למחוק / להסיר מ-Git

אחרי מעבר ל-Docker והגדרת Render עם שני שירותים:

- **`frontend/dist/`** – אפשר למחוק מהדיסק ולהסיר מ-Git (`.gitignore` כבר יכול לכלול `frontend/dist`). הבנייה מתבצעת ב-Docker וב-Render.
- **`Dockerfile`** בשורש הפרויקט – אפשר למחוק; הבנייה מתבצעת מ-`backend/Dockerfile` ו-`frontend/Dockerfile`.

ראה **`frontend/README.md`** לסקריפטים והרצת פיתוח.

## Backend – Layered Architecture

- **`backend/ARCHITECTURE.md`** — סכמה (Mermaid) והסבר על השכבות
- **Presentation** (`app/`): `main.py` (חיבור בלבד), `api/`, `routes/` (כולל **`routes/health.py`** – health ייעודי), `bot/`. ה-Web App **לא** מוגש מהבקאנד – `/game` מפנה ל-`WEBAPP_URL`.
- **Application** (`services/`): `game_session.py` — לוגיקת משחק
- **Domain** (`domain/`): `game.py` — סכמה (`GameStateResponse`, `HealthResponse`)
- **Infrastructure**: `config.py` (כולל `MODE`), `utils/urls.py`
- `render.yaml` — הגדרת Blueprint ל-Render
