# משימות – פריסה ל-Render (להעתיק ולבצע לפי הסדר)

---

## שלב 1: בניית הפרונט והעלאה ל-GitHub

(אם כבר הרצת והעלית – דלג ל־שלב 2.)

1. פתח טרמינל בתיקיית הפרויקט.

2. בנה את הפרונט:
```bash
cd frontend
npm run build
cd ..
```

3. הוסף את תוצאת הבנייה ל-Git:
```bash
git add frontend/dist
git status
```
(וודא ש־`frontend/dist` מופיע ברשימה.)

4. commit ו-push:
```bash
git commit -m "build: frontend for Render"
git push
```

---

## שלב 2: יצירת שירות ב-Render

1. היכנס ל־https://render.com והתחבר.

2. לחץ **New** → **Blueprint**.

3. חבר את ה-repository של GitHub (אם עדיין לא חיברת – Authorize Render ב-GitHub ובחר את ה-repo).

4. Render יזהה את `render.yaml`. אשר את השירות ולחץ **Apply** / **Deploy Blueprint**.

5. חכה לסיום ה-Deploy (סטטוס "Live" בירוק).

---

## שלב 3: הגדרת משתני סביבה ב-Render

1. ב-Render: בחר את השירות (telegram-bot).

2. בתפריט השמאלי: **Environment**.

3. לחץ **Add Environment Variable** והוסף אחד־אחד:

| Key | Value |
|-----|--------|
| `TELEGRAM_TOKEN` | הטוקן שקיבלת מ־@BotFather |
| `WEBAPP_URL` | הכתובת של השירות (למשל `https://telegram-bot-xxxx.onrender.com`) – **בלי** סלאש בסוף |
| `REDIS_URL` | (אופציונלי) אם הוספת Redis ב-Render – העתק את ה-URL; אחרת השאר ריק |

4. שמור (Save Changes). Render יעשה Redeploy אוטומטי.

---

## שלב 4: בדיקה

1. אחרי שה-Deploy מסתיים, פתח בדפדפן:
   `https://<שם-השירות-שלך>.onrender.com/health`
   אמור להחזיר משהו כמו: `{"status":"awake","mode":"production"}`.

2. פתח:
   `https://<שם-השירות-שלך>.onrender.com/game`
   אמור להיפתח דף המשחק (לא JSON).

3. בטלגרם: פתח את הבוט → התחל משחק בקבוצה → "שחק עכשיו" / הלינק מהבוט – אמור לפתוח את דף המשחק ב-Render.

---

## אם משהו לא עובד

- **דף /game מחזיר JSON "קובץ המשחק לא נמצא":** הרץ שוב את שלב 1 (בניית פרונט + `git add frontend/dist` + commit + push) ו-Redeploy ב-Render.
- **הבוט לא מגיב:** וודא ש־`TELEGRAM_TOKEN` נכון ו־`WEBAPP_URL` מוגדר (כתובת ה-Render **בלי** סלאש). אחרי שינוי ב-Environment Render עושה Redeploy.
- **"משחק לא נמצא" כשפותחים לינק:** וודא ש־Redis רץ (אם הוספת Redis ב-Render – `REDIS_URL` מוגדר). בלי Redis המשחקים נשמרים רק בזיכרון ויכולים להיעלם אחרי sleep.
