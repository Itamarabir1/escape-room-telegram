# pyright: reportMissingImports=false
"""Safe puzzle: Caesar shift (ASCII +3). Used for the unlock item."""

CAESAR_SHIFT = 3

# Backstory for the safe (Hebrew). Shown in the modal.
SAFE_BACKSTORY = (
    "חידה 3: כספת חדר השרתים\n\n"
    "הסיטואציה: חדר השרתים התקול ננעל! הכספת שבתוכו מכילה את רכיב הגיבוי הקריטי, "
    "אך היא מוגנת בצופן שהמערכת יצרה באופן אוטומטי לפני הקריסה.\n\n"
    "הקוד שהופיע על המסוף הוא: 78-72-92\n\n"
    "המשימה: השתמשו בכוח ההיגיון כדי לפענח את הקשר בין המספרים ולהכניס את סיסמת הפריצה לכספת.\n\n"
    "השתמשו במספר הסודי כדי לפתור את החידה."
)

PROMPT_TEXT = "הכניסו את סיסמת הפריצה לכספת:"

SUCCESS_MESSAGE = "הכספת נפתחה! הרמז שבתוכה מוביל לפריט הבא בחדר."
WRONG_MESSAGE = "סיסמה שגויה, נסה שוב."


def caesar_encode(password: str, shift: int = CAESAR_SHIFT) -> str:
    """Encode password: each char -> ASCII code + shift, joined by '-' (e.g. KEY -> 78-72-92)."""
    if not password or not password.strip():
        return ""
    codes = [ord(c) + shift for c in password.strip()]
    return "-".join(str(c) for c in codes)


def normalize_answer(answer: str) -> str:
    """Strip and lowercase for comparison (e.g. KEY/key/Key → key)."""
    return (answer or "").strip().lower()
