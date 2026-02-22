# pyright: reportMissingImports=false
"""Demo room: fixed items and puzzles for testing without AI/image.
All task content and correct answers live here (backend); validation is always server-side.
Positions (x,y) mimic where objects will sit on the real image later."""

from utils.puzzle import CAESAR_SHIFT, PROMPT_TEXT, SAFE_BACKSTORY, caesar_encode

# Room canvas size used for placeholder (same ratio as typical room image)
DEMO_ROOM_WIDTH = 800
DEMO_ROOM_HEIGHT = 600

DEMO_ROOM_ITEMS = [
    {"id": "safe_1", "label": "כספת", "x": 320, "y": 220, "action_type": "unlock"},
    {"id": "picture_wall", "label": "תמונה על הקיר", "x": 120, "y": 80, "action_type": "examine"},
    {"id": "carpet", "label": "שטיח", "x": 380, "y": 420, "action_type": "examine"},
]

SAFE_PASSWORD = "KEY"

DEMO_ROOM_PUZZLES = {
    "safe_1": {
        "type": "unlock",
        "backstory": SAFE_BACKSTORY,
        "encoded_clue": caesar_encode(SAFE_PASSWORD, CAESAR_SHIFT),
        "correct_answer": SAFE_PASSWORD,
        "prompt_text": PROMPT_TEXT,
    },
    "picture_wall": {
        "type": "examine",
        "backstory": (
            "תמונה תלויה על הקיר. במסגרת רשום מספר שמופיע גם בכספת. "
            "חפשו רמזים בחדר – אולי הקוד שפותר את הכספת."
        ),
    },
    "carpet": {
        "type": "examine",
        "backstory": (
            "שטיח מכסה את הרצפה. מתחתיו אולי מסתתר רמז, "
            "אבל כרגע עדיף להתמקד בכספת ובתמונה על הקיר."
        ),
    },
}

# טקסט הסיטואציה – מוקרא בפתיחת הדף (TTS) ומוצג למשתמש
DEMO_ROOM_SITUATION = (
    "אתם נכנסים לחדר בריחה themed מדעי המחשב. "
    "בחדר יש כספת, תמונה על הקיר ושטיח. חפשו רמזים ופענחו את הסיסמה."
)

DEMO_ROOM_META = {
    "room_name": "חדר בריחה",
    "room_description": "חדר לדוגמה – לחץ על הפריטים לפתיחת משימות.",
    "room_lore": DEMO_ROOM_SITUATION,
}
