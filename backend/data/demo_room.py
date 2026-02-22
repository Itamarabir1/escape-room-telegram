# pyright: reportMissingImports=false
"""Demo room: fixed items and puzzles for testing without AI/image.
All task content and correct answers live here (backend); validation is always server-side.
Positions (x,y) mimic where objects will sit on the real image later."""

from utils.puzzle import CAESAR_SHIFT, PROMPT_TEXT, SAFE_BACKSTORY, caesar_encode

# Room canvas size – גדול מהמסך כדי שיהיה צורך לגלול ימינה/שמאלה (פנורמה)
DEMO_ROOM_WIDTH = 1600
DEMO_ROOM_HEIGHT = 1200

DEMO_ROOM_ITEMS = [
    {"id": "safe_1", "label": "כספת", "x": 640, "y": 440, "action_type": "unlock"},
    {"id": "picture_wall", "label": "תמונה על הקיר", "x": 240, "y": 160, "action_type": "examine"},
    {"id": "carpet", "label": "שטיח", "x": 760, "y": 840, "action_type": "examine"},
    {"id": "board_servers", "label": "לוח חשמל", "x": 1000, "y": 300, "action_type": "unlock"},
    {"id": "clock_1", "label": "שעון", "x": 200, "y": 600, "action_type": "unlock"},
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
    "אתם נכנסים לחדר בריחה themed מדעי המחשב. "
    "בחדר יש כספת, תמונה על הקיר ושטיח. חפשו רמזים ופענחו את הסיסמה."
)

DEMO_ROOM_META = {
    "room_name": "חדר בריחה",
    "room_description": "חדר לדוגמה – לחץ על הפריטים לפתיחת משימות.",
    "room_lore": DEMO_ROOM_SITUATION,
}
