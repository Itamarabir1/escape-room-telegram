# pyright: reportMissingImports=false
"""Safe puzzle: Caesar shift (ASCII +3). Used for the unlock item."""

CAESAR_SHIFT = 3

# Backstory for the safe (Hebrew). Shown in the modal.
SAFE_BACKSTORY = (
    "כספת חדר השרת התקול מוגנת בסיסמה שהמערכת יצרה. "
    "במקום להקליד את הסיסמה ישר, עליכם לפענח את הצופן שבו היא מוצפנת. "
    "אם תצליחו, הכספת תפתח ותגלו את הרמז שבתוכה."
)

PROMPT_TEXT = "השתמשו בכוח ההגיון כדי לפענח את הסיסמה ולהכניס אותה בכספת."

SUCCESS_MESSAGE = "הכספת נפתחה! הרמז שבתוכה מוביל לפריט הבא בחדר."
WRONG_MESSAGE = "סיסמה שגויה, נסה שוב."


def caesar_encode(password: str, shift: int = CAESAR_SHIFT) -> str:
    """Encode password: each char -> ASCII code + shift, joined by '-' (e.g. KEY -> 78-72-92)."""
    if not password or not password.strip():
        return ""
    codes = [ord(c) + shift for c in password.strip()]
    return "-".join(str(c) for c in codes)


def normalize_answer(answer: str) -> str:
    """Strip and uppercase for comparison."""
    return (answer or "").strip().upper()
