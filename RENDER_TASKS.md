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

## Cron-job.org (כדי שהשרת לא יירדם)

ב-Render Free ה-instance נרדם אחרי ~15 דקות ללא תנועה. כדי להשאיר אותו ער, הגדר ב-[Cron-job.org](https://cron-job.org) קריאה **כל 14 דקות** (או פחות) ל-endpoint ה-health:

- **כתובת:** `https://escape-room-telegram.onrender.com/health`  
  (אם שם השירות שלך ב-Render שונה – החלף את `escape-room-telegram` בשם השירות שלך.)
- **שיטה:** GET (ללא auth).
- **Timeout:** **חשוב:** אחרי שינה הבקשה הראשונה לוקחת 30–60 שניות. ב-Cron-job.org בהגדרות ה-job הגדר **Timeout 90 שניות** (או לפחות 60). בלי זה הבקשה נכשלת והשרת לא מתעורר.
- **תדירות:** כל 14 דקות (או 10) – חייב לפני 15 דקות ללא תנועה.

---

## עדכון פרונט (תמונה, טיימר, כפתורים וכו')

**אם שינית קוד בפרונט (frontend) והלינק מטלגרם עדיין מציג גרסה ישנה:**

1. בנה מחדש את הפרונט:
   ```bash
   cd frontend
   npm run build
   cd ..
   ```
2. הוסף את התוצאה ל-Git והעלה:
   ```bash
   git add frontend/dist
   git commit -m "build: frontend update (room image, timer, etc.)"
   git push
   ```
3. ב-Render יופעל Redeploy אוטומטי. אחרי סיום, פתח את הלינק מטלגרם מחדש (או רענן קשיח / פתח בחלון פרטי) כדי לראות את הגרסה החדשה.

---

## אם משהו לא עובד

- **דף /game מחזיר JSON "קובץ המשחק לא נמצא":** הרץ שוב את שלב 1 (בניית פרונט + `git add frontend/dist` + commit + push) ו-Redeploy ב-Render.
- **הלינק מטלגרם מציג גרסה ישנה (בלי תמונה, עם כפתורים ישנים):** הרץ "עדכון פרונט" למעלה – בניית frontend, commit ל־frontend/dist ו-push. וודא שב-Cron-job.org ה-Timeout הוא 90 שניות.
- **הבוט לא מגיב:** וודא ש־`TELEGRAM_TOKEN` נכון ו־`WEBAPP_URL` מוגדר (כתובת ה-Render **בלי** סלאש). אחרי שינוי ב-Environment Render עושה Redeploy.
- **"משחק לא נמצא" כשפותחים לינק:** וודא ש־Redis רץ (אם הוספת Redis ב-Render – `REDIS_URL` מוגדר). בלי Redis המשחקים נשמרים רק בזיכרון ויכולים להיעלם אחרי sleep.
- **השרת נרדם:** וודא ש-Cron-job.org קורא ל־`/health` **כל 14 דקות**, כתובת מלאה, ו-**Timeout 90 שניות** (בהגדרות ה-job).
