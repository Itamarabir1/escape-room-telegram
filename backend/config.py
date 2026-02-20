import os
from dotenv import load_dotenv

# טעינת הקובץ פעם אחת בלבד
load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GAME_DIFFICULTY = os.getenv("GAME_DIFFICULTY", "Normal") # אפשר לשים ערכי ברירת מחדל
    
    # בדיקת תקינות - אם אין טוקן, האפליקציה לא תעלה
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ שגיאה: המשתנה TELEGRAM_TOKEN חסר בקובץ .env")

# יצירת מופע אחד של הקונפיג לשימוש בכל הפרויקט
config = Config()