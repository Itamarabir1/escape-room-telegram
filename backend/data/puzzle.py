# pyright: reportMissingImports=false
"""Puzzle game content: Caesar encoding, messages, and dependency rules (order of solving)."""

CAESAR_SHIFT = 3

# Backstory for the safe (Hebrew). Shown in the modal. The code is shown separately in the modal (encoded_clue); under it the frontend shows "השתמשו גם במספר הסודי" for safe_1.
SAFE_BACKSTORY = (
    "כספת חדר השרתים\n\n"
    "הסיטואציה: חדר השרתים התקול ננעל! הכספת שבתוכו מכילה את רכיב הגיבוי הקריטי, "
    "אך היא מוגנת בצופן שהמערכת יצרה באופן אוטומטי לפני הקריסה.\n\n"
    "המשימה: השתמשו בכוח ההיגיון כדי לפענח את הקשר בין המספרים ולהכניס את סיסמת הפריצה לכספת."
)

PROMPT_TEXT = "הכניסו את סיסמת הפריצה לכספת:"

SUCCESS_MESSAGE = "הכספת נפתחה!"

# הודעות הצלחה לפי פריט (כשפותרים חידת unlock). אם item_id לא ברשימה – משתמשים ב-SUCCESS_MESSAGE.
ITEM_SUCCESS_MESSAGES: dict[str, str] = {
    "clock_1": "השעון כוון בהצלחה",
    "board_servers": "לוח הבקרה נפתח!",
    "safe_1": "הכספת נפתחה בהצלחה, בתוכה יש מפתח",
}

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


# --- Puzzle dependencies (order: which item_id requires others solved first) ---
# item_id -> list of item_ids that must be SOLVED before this one can be solved
PUZZLE_DEPENDENCIES: dict[str, list[str]] = {
    "board_servers": ["clock_1"],
}

DEPENDENCY_BLOCK_MESSAGES: dict[str, str] = {
    "board_servers": "כוונו את השעון כדי לפתוח את לוח הבקרה.",
}


def get_puzzle_dependencies(room_id: str | None = None) -> dict[str, list[str]]:
    """Return dependencies for the given room. For now only demo room; room_id ignored."""
    return dict(PUZZLE_DEPENDENCIES)


def get_dependencies_for_item(item_id: str, room_id: str | None = None) -> list[str]:
    """Return item_ids that must be solved before item_id can be solved."""
    deps = get_puzzle_dependencies(room_id)
    return list(deps.get(item_id) or [])


def get_block_message(item_id: str) -> str:
    """User-facing message when item_id is blocked by unmet dependencies."""
    return DEPENDENCY_BLOCK_MESSAGES.get(
        item_id, "יש לפתור קודם חידות אחרות בחדר."
    )
