# pyright: reportMissingImports=false
"""Demo room: fixed items and puzzles for testing without AI/image.
All task content and correct answers live here (backend); validation is always server-side.
Positions (x,y) mimic where objects will sit on the real image later."""

from utils.puzzle import CAESAR_SHIFT, PROMPT_TEXT, SAFE_BACKSTORY, caesar_encode

# Room canvas size – גדול מהמסך כדי שיהיה צורך לגלול ימינה/שמאלה (פנורמה)
DEMO_ROOM_WIDTH = 1280
DEMO_ROOM_HEIGHT = 768

DEMO_ROOM_ITEMS = [
    {"id": "door", "label": "דלת", "x": 678, "y": 138, "action_type": "examine"},
    {"id": "safe_1", "label": "כספת", "x": 512, "y": 282, "action_type": "unlock"},
    {"id": "picture_wall", "label": "תמונה על הקיר", "x": 192, "y": 102, "action_type": "examine"},
    {"id": "carpet", "label": "שטיח", "x": 608, "y": 538, "action_type": "examine"},
    {"id": "board_servers", "label": "לוח בקרה", "x": 141, "y": 23, "action_type": "unlock"},
    {"id": "clock_1", "label": "שעון", "x": 538, "y": 92, "action_type": "unlock"},
]

SAFE_PASSWORD = "KEY"

DEMO_ROOM_PUZZLES = {
    "door": {
        "type": "examine",
        "backstory": "הדלת נעולה. צריך למצוא מפתח או קוד כדי לצאת מהחדר. חפשו רמזים בכספת, בשעון ובלוח הבקרה.",
    },
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
    "board_servers": {
        "type": "unlock",
        "backstory": (
            "לוח השרתים – \"מי באותה רשת?\"\n\n"
            "על הקיר יש לוח עם כתובות IP של מכשירים בחדר:\n\n"
            "192.168.1.12\n192.168.1.45\n192.168.2.7\n192.168.1.99\n\n"
            "ומתחת כתוב: Only devices in the same subnet can communicate.\n\n"
            "רמז: Subnet Mask: 255.255.255.0\n\n"
            "255.255.255.0 אומר ששלושת האוקטטים הראשונים מגדירים רשת. "
            "כמה מכשירים יכולים לתקשר זה עם זה? (הכנס מספר.)"
        ),
        "correct_answer": "3",
        "prompt_text": "הכנס את מספר המכשירים באותה רשת:",
    },
    "clock_1": {
        "type": "unlock",
        "backstory": (
            "חידת השעון – \"פגישה מושלמת בדקות שלמות\"\n\n"
            "בחדר יש שעון עם מחוגים:\n"
            "• המחוג הקטן (שעות) זז 0.5° לדקה\n"
            "• המחוג הגדול (דקות) זז 6° לדקה\n\n"
            "שאלה: אחרי כמה דקות המחוגים יהיו שוב בדיוק על אותו המקום בו התחילו (12:00), "
            "בדיוק בדקות שלמות?\n\n"
            "רמז: זווית המחוג הקטן θh = 0.5×m, המחוג הגדול θm = 6×m. "
            "מחפשים m כך ש-θh ≡ θm (mod 360). כלומר 5.5m = 360×k, m = 720×k/11. "
            "בחר k כך ש-m יהיה מספר שלם של דקות."
        ),
        "correct_answer": "720",
        "prompt_text": "הכנס את מספר הדקות (מספר שלם):",
    },
}

# טקסט הסיטואציה – מוקרא בפתיחת הדף (TTS) ומוצג למשתמש
DEMO_ROOM_SITUATION = (
    "הדלת נטרקה מאחוריכם. בחושך יש רק את טיקטוק השעון והצללים על הקיר. "
    "הזמן בורח — תפענחו את הרמזים ותמצאו את הדרך החוצה לפני שיהיה מאוחר מדי."
)

DEMO_ROOM_META = {
    "room_name": "חדר בריחה",
    "room_description": "חדר לדוגמה – לחץ על הפריטים לפתיחת משימות.",
    "room_lore": DEMO_ROOM_SITUATION,
}
