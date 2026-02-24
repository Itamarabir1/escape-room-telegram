# פרומפט: הפרדה בין הכפתור לטקסט במודל ההתחלה

## בעברית (לשימוש ישיר)

במסך ההתחלה של המשחק (הכפתור "התחל" והטקסט מתחתיו) – **הטקסט יושב על הכפתור** או צמוד מדי אליו. אני רוצה ש**הטקסט יהיה בשורה מתחת לכפתור** עם ריווח ברור, **שאף אחד לא יסתיר את השני**: לא הכפתור את הטקסט ולא הטקסט את הכפתור.

עדכן את ה-CSS ב-`frontend/src/index.css`:
- עבור `.room-start-ui` – וודא פריסה אנכית ברורה: `display: flex`, `flex-direction: column`, `align-items: center`, ו-**ריווח מספיק** בין הכפתור לפסקה (למשל `gap` גדול יותר או `margin-top` לפסקה).
- עבור `.room-situation-below-btn` – הוסף `margin-top` מספיק (למשל 14px או 16px) כדי שהטקסט יישב **מתחת** לכפתור ולא יידבק אליו.
- וודא שהכפתור `.room-start-btn` נשאר לחיץ ונראה במלואו, והטקסט מתחתיו גלוי במלואו בלי חפיפה.

---

## In English (for Cursor)

In the game start overlay, the **text sits on or too close to the button**. I want the **text to sit clearly on a line below the button** so that **neither element hides the other**.

Update the CSS in `frontend/src/index.css`:
- For `.room-start-ui`: ensure a clear vertical stacked layout with `display: flex`, `flex-direction: column`, `align-items: center`, and **enough spacing** between the button and the paragraph (e.g. larger `gap` or `margin-top` on the text).
- For `.room-situation-below-btn`: add sufficient `margin-top` (e.g. 14px or 16px) so the text sits **below** the button and does not overlap or touch it.
- Ensure the `.room-start-btn` button remains fully visible and clickable, and the text below is fully visible with no overlap.
