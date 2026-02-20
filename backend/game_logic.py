class LogicEngine:
    def __init__(self):
        # כאן אפשר לאתחל את ה-Client של OpenAI או Gemini
        pass

    def generate_story_start(self, players):
        """יוצר את תחילת הסיפור בהתבסס על רשימת השחקנים"""
        player_names = ", ".join(players.values())
        prompt = f"צור התחלה למשחק הרפתקאות עבור הגיבורים: {player_names}. תאר את המקום שבו הם נמצאים."
        
        # כאן תבוא הקריאה ל-API של ה-AI. כרגע נחזיר טקסט דוגמה:
        return f"🌟 ההרפתקה מתחילה!\nהחבורה הכוללת את {player_names} עומדת בשער של טירה עתיקה..."

    def process_action(self, player_name, action_text, history):
        """מעבד פעולה של שחקן ומחזיר את תגובת העולם"""
        # כאן ה-AI יקבל את מה שהשחקן כתב ויחליט מה קרה
        return f"*{player_name}* ניסה {action_text}. פתאום, נשמע קול נפץ!"