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

## שלב 3: Redis ב-Render (חובה – state קבוע)

1. ב-Render: **Dashboard** → השירות שלך (escape-room-telegram וכו').
2. בתפריט השמאלי: **Environment**.
3. **הוספת Redis:**
   - לחץ **Add Integration** (או **Add New** → **Redis**).
   - צור Redis instance. Render יזריק אוטומטית משתנה `REDIS_INTERNAL_URL` (או `REDIS_URL`) לשירות שלך.
4. הקוד תומך גם ב־`REDIS_INTERNAL_URL` (ברירת מחדל של Render) – אין חובה להגדיר `REDIS_URL` ידנית אם הוספת Redis addon.
5. אם Redis לא הוזן אוטומטית: הוסף משתנה **Key:** `REDIS_URL`, **Value:** ה-URL שמופיע ב-Redis addon (למשל `redis://red-xxxx:6379`).
6. שמור (Save Changes). Render יעשה Redeploy אוטומטי – הלוג "Redis not available" / "Connection refused" אמור להיעלם.

## שלב 3ב: שאר משתני הסביבה

| Key | Value |
|-----|--------|
| `TELEGRAM_TOKEN` | הטוקן שקיבלת מ־@BotFather |
| `WEBAPP_URL` | הכתובת של השירות (למשל `https://escape-room-telegram.onrender.com`) – **בלי** סלאש בסוף |
| `REDIS_URL` | (אופציונלי) רק אם Redis addon לא הזריק אוטומטית – העתק את ה-URL מ-Redis addon |

שמור (Save Changes).

---

## שלב 4: בדיקה מהירה

1. אחרי שה-Deploy מסתיים, פתח בדפדפן:
   ```
   https://escape-room-telegram.onrender.com/health
   ```
   אמור להחזיר: `{"status":"awake","mode":"production"}` (או דומה).

2. פתח:
   ```
   https://escape-room-telegram.onrender.com/game
   ```
   אמור להיפתח דף המשחק (לא JSON).

3. **בדיקת Redis:** בטלגרם – פתח את הבוט → התחל משחק בקבוצה → "שחק עכשיו" / הלינק מהבוט. אמור לפתוח את דף המשחק ב-Render; אם מופיע "משחק לא נמצא" – וודא ש-Redis addon מחובר ו־REDIS_INTERNAL_URL או REDIS_URL מוגדרים, ואז Redeploy.

---

## Cron-job.org (כדי שהשרת לא יירדם) – חובה

ב-Render Free ה-instance **נרדם אחרי ~15 דקות** ללא תנועה. אם אין קריאה ל־/health לפחות כל 14 דקות, השרת יירדם והבקשה הראשונה אחרי זה תכשל (או תתעכב 30–60 שניות).

### הגדרה ב-[cron-job.org](https://cron-job.org)

1. **צור חשבון** (חינם) והתחבר.
2. **Create Cronjob** (או "Add cron job").
3. **כתובת (URL):**  
   `https://<שם-השירות-שלך>.onrender.com/health`  
   (החלף בשם האמיתי של השירות ב-Render, למשל `telegram-bot-xxxx.onrender.com`.)
4. **שיטה:** GET. אל תבחר POST.
5. **תדירות:** **כל 10 דקות** (או לכל היותר כל 14 דקות). אם התדירות מעל 14 דקות, השרת עלול להירדם לפני הבקשה הבאה.
6. **Timeout – קריטי:**  
   אחרי שינה, ה־instance מתעורר בערך 30–60 שניות. אם ל-Cron יש timeout קצר (למשל 30 שניות), הבקשה תיכשל והשרת לא ייחשב "ער".  
   **הגדר Timeout ל־90 שניות** (בהגדרות המתקדמות של ה-job ב-cron-job.org). בלי זה השרת ימשיך "להירדם".
7. שמור את ה-job ובדוק ב-**Log** או **History** שהקריאות מצליחות (סטטוס 200).

### אם השרת עדיין נרדם – checklist

- [ ] ה-URL ב-Cron הוא **בדיוק** כתובת ה-Render + `/health` (כולל https).
- [ ] ה-job **רץ בפועל** כל 10–14 דקות (בדוק ב-History / Log ב-cron-job.org).
- [ ] **Timeout = 90 שניות** (או 120). לא 30 ולא 60.
- [ ] אין חוסם (firewall/VPN) שמונע מ-cron-job.org להגיע ל-Render.
- [ ] אפשר ליצור **job שני** (למשל כל 5 דקות) כגיבוי – Render לא מגביל כמות קריאות.

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
- **השרת נרדם:** ראה למעלה את הקטע "Cron-job.org" וה-checklist. חובה: **כל 10–14 דקות**, **Timeout 90 שניות**, ו-URL נכון. בדוק ב-cron-job.org ב-History שהקריאות מחזירות 200.
