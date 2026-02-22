# הרצת הבאקאנד (Backend)

הפרויקט רץ עם **uv** – אין צורך בסביבה וירטואלית ידנית או ב-`activate`. כל ההתקנות וההרצה דרך uv.

**חובה:** להריץ Redis לפני הבאקאנד – אחרת משחקים ושחקנים (טלגרם + Web) לא יסתנכרנו.

---

## Redis (לפני הרצת הבאקאנד)

מהשורש של הפרויקט:

```powershell
cd c:\Users\user\Desktop\telegram-bot
docker compose up -d redis
```

בלי Redis הבאקאנד לא ימצא משחקים שנפתחו מטלגרם, וה-Web יראה "אין שחקנים".

---

## פעם ראשונה (התקנת תלויות)

```powershell
cd c:\Users\user\Desktop\telegram-bot\backend
uv sync
```

---

## הרצת השרת

```powershell
cd c:\Users\user\Desktop\telegram-bot\backend
uv run uvicorn app.main:app --reload --reload-exclude ".venv" --host 0.0.0.0 --port 8000
```

זהו. uv מטפל בתלויות ובסביבה – אתה רק מריץ את הפקודה.

---

## סיכום

| מה לעשות | פקודה |
|----------|--------|
| הפעלת Redis | `docker compose up -d redis` (משורש הפרויקט) |
| התקנה / עדכון תלויות | `uv sync` (מתוך `backend`) |
| הרצת הבאקאנד | `uv run uvicorn app.main:app --reload --reload-exclude ".venv" --host 0.0.0.0 --port 8000` (מתוך `backend`) |

מקור התלויות: `pyproject.toml`. משחקים ושחקנים נשמרים ב-Redis – חייבים להריץ Redis כדי שטלגרם וה-Web יראו את אותו מצב.

**חדר:** אין יצירת תמונה בזמן אמת. נטען חדר עם מיקומי כפתורים (כספת, תמונה על הקיר, שטיח); תמונה סטטית אפשר להוסיף בהמשך. ראה `data/demo_room.py` ו־`docs/GAME_STATE_ARCHITECTURE.md`.

**אחרי שינויי פרונט:** הרץ `cd frontend && npm run build` – הבאקאנד מגיש קבצים מ־`frontend/dist`; בלי בנייה מחדש הדפדפן ימשיך להציג גרסה ישנה.

**הלינק מהטלגרם עדיין מוביל למסך הישן?**
- הלינק נקבע לפי `WEBAPP_URL` ב־`.env` (או `http://localhost:8000` אם לא הוגדר).
- **אם אתה פותח לוקלית:** וודא ש־`WEBAPP_URL` **לא** מוגדר (או ריק). הרץ `cd frontend && npm run build`, הפעל את הבאקאנד, ופתח בדפדפן: `http://localhost:8000/game?game_id=...` (ה־game_id מההודעה של הבוט).
- **אם הלינק מהטלגרם פונה לשרת מרוחק (למשל Render):** השרת מגיש את ה־dist שהיה בזמן הדיפלוי. צריך לבנות את הפרונט ואז לעדכן את הפריסה (להעלות את תיקיית `frontend/dist` המעודכנת או להריץ build כחלק מ־deploy).
