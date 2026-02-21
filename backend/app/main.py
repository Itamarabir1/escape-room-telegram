import logging
from telegram.ext import ApplicationBuilder
from config import config
from game_manager import GameManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    # יצירת האפליקציה
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    # אתחול המנהל - הוא כבר ידאג לרשום את כל ה-Handlers
    game_manager = GameManager(app)

    print("🚀 המנהל (Manager) התניע את הבוט!")
    app.run_polling()

if __name__ == '__main__':
    main()