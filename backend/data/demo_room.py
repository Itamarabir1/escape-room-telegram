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

# For encoding the clue (78-72-92); comparison uses lowercase "key"
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
        "correct_answer": "key",
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
            "לוח הבקרה – \"פרוטוקול התקשורת\"\n\n"
            "הסיטואציה: המערכת המרכזית נעולה. כדי לפרוץ אותה, עליכם למצוא את \"קבוצת העבודה\" (Subnet) "
            "הגדולה ביותר בחדר השרתים. על לוח הבקרה מופיעות כתובות ה-IP הבאות:\n\n"
            "Node-01: 192.168.1.12\n"
            "Node-02: 192.168.1.45\n"
            "Node-03: 192.168.2.7\n"
            "Node-04: 192.168.1.99\n\n"
            "הנתונים: התקשורת בחדר מתבצעת תחת הגדרת Subnet Mask: 255.255.255.0.\n\n"
            "המשימה: רק מכשירים השייכים לאותה תת-רשת (Subnet) מסוגלים לתקשר ולהעביר נתונים ביניהם. "
            "כמה מכשירים מצאתם שיכולים ליצור רשת אחת מאוחדת?\n\n"
            "המספר שתקבלו הוא המספר המיוחד/הסודי של החדר – תשמרו אותו לשלב הבא."
        ),
        "correct_answer": "3",
        "correct_answer_aliases": ["שלוש"],
        "prompt_text": "הכניסו את מספר המכשירים באותה רשת (זהו המספר הסודי):",
    },
    "clock_1": {
        "type": "unlock",
        "backstory": (
            "השעון – \"הפגישה המושלמת\"\n\n"
            "הסיטואציה: משהו מוזר קורה לזמן בחדר השרתים. השעון האנלוגי שעל הקיר נעצר בדיוק ב-12:00. "
            "כדי לאתחל את המערכת, עליכם לחשב מתי המחוגים ייפגשו שוב בנקודה שבה הם מצביעים בדיוק על אותה דקה שלמה.\n\n"
            "נתוני המנגנון:\n"
            "• המחוג הקטן (שעות) מתקדם ב-0.5° בכל דקה.\n"
            "• המחוג הגדול (דקות) מתקדם ב-6° בכל דקה.\n\n"
            "האתגר: עליכם למצוא את מספר הדקות השלם הראשון (m) שבו שני המחוגים יהיו שוב בדיוק באותו מקום.\n\n"
            "(רמז למתכנתים: אנחנו מחפשים מספר דקות שלם m כך שההפרש בין הזוויות שלהם יהיה כפולות של סיבוב שלם, כלומר 360×k.)\n\n"
            "המשימה: בעוד כמה דקות (מספר שלם) יצטלבו המחוגים שוב במיקום זהה?"
        ),
        "correct_answer": "720",
        "prompt_text": "הכניסו את מספר הדקות:",
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
