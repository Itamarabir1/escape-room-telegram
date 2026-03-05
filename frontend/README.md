# Frontend

פרויקט Vite + React + TypeScript. **הפרונט נמצא רק כאן** — אין קוד backend בתיקייה זו.

## מבנה תיקיות

| תיקייה | תפקיד |
|--------|--------|
| `src/pages/` | דפים (GamePage – דף המשחק היחיד). |
| `src/components/` | קומפוננטות: Banners, DoorVideoOverlay, RoomView, ScienceLabRoom, TaskModal. |
| `src/api/` | `client.ts` – מקור יחיד לקריאות API, טיפוסי תגובה (GameStateResponse וכו'), וקבועי חדר (DEMO_ROOM_*). |
| `src/constants/` | הודעות למשתמש (messages), צורות hotspots וטיימר (roomHotspots). |
| `src/utils/` | עזרים על מצב משחק (gameHelpers: getPuzzles, getPuzzleByItemId). |
| `dist/` | תוצאת בנייה (נוצר אחרי `npm run build`); הבקאנד מגיש ב-`/static` ו-`/game`. |

## סקריפטים

- **`npm run dev`** — שרת פיתוח (פורט 5173) עם proxy של `/api` ל-backend (ברירת מחדל `http://localhost:8000`)
- **`npm run build`** — בנייה ל-`dist/` (חובה לפני פרודקשן)
- **`npm run preview`** — תצוגה מקומית של ה-dist

## הפרדה מהבקאנד

- הבקאנד נמצא ב-`backend/` ומגיש רק API ו-**קבצים בנויים** מ-`frontend/dist`.
- הפרונט מדבר עם הבקאנד רק דרך HTTP (משתנה סביבה `VITE_API_URL` — ריק = same-origin).

## פרודקשן

1. `cd frontend && npm run build`
2. הפעלת הבקאנד — הוא יגיש את `frontend/dist` ב-`/static` וב-`/game`.