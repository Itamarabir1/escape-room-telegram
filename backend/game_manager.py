from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

class GameManager:
    def __init__(self, application):
        self.app = application
        self.setup_handlers()

    def setup_handlers(self):
        """רישום כל המאזינים של הבוט"""
        self.app.add_handler(CommandHandler("start_game", self.start_game))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.welcome_new_member))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_any_message))

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 1. בדיקה אם כבר יש משחק - אם כן, אל תעשה כלום
        if context.chat_data.get('game_active'):
            await update.message.reply_text("המשחק כבר התחיל! אי אפשר להירשם שוב כרגע. ✋")
            return

        # 2. אתחול נקי
        context.chat_data['players'] = {}
        
        # 3. יצירת הכפתור
        keyboard = [[InlineKeyboardButton("אני רוצה לשחק! 🙋‍♂️", callback_data='join_game')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 4. שליחת הודעה *אחת* בלבד
        sent_message = await update.message.reply_text(
            "🎮 **ההרפתקה מתחילה!**\n\nמי מצטרף אלינו היום? לחצו על הכפתור למטה כדי להירשם.", 
            reply_markup=reply_markup
        )
        context.chat_data['registration_msg_id'] = sent_message.message_id

    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """הלוגיקה שביקשת: הצעה למצטרפים חדשים"""
        for new_user in update.message.new_chat_members:
            if new_user.is_bot: continue
            
            keyboard = [[
                InlineKeyboardButton("כן ✅", callback_data='join_game'),
                InlineKeyboardButton("לא ❌", callback_data='ignore_welcome')
            ]]
            await update.message.reply_text(
                f"אהלן {new_user.first_name}! רוצה להצטרף למשחק?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user = query.from_user
        await query.answer()

        # 1. הצטרפות למשחק
        if query.data == 'join_game':
            # בדיקת בטיחות: האם המשחק כבר התחיל בזמן שמישהו ניסה ללחוץ?
            if context.chat_data.get('game_active'):
                await query.answer("מצטערים, ההרשמה נסגרה! המשחק כבר התחיל. 🏃‍♂️", show_alert=True)
                return

            if 'players' not in context.chat_data: 
                context.chat_data['players'] = {}
            
            # מניעת כפילות: בודק אם השחקן כבר רשום
            if user.id in context.chat_data['players']:
                await query.answer("אתה כבר רשום למשחק! 😉", show_alert=True)
                return

            # הוספת השחקן לרשימה
            context.chat_data['players'][user.id] = user.first_name
            
            # בניית רשימת השמות המעודכנת
            players_list = "\n".join([f"- {name}" for name in context.chat_data['players'].values()])
            
            # יצירת כפתורים (משאירים את האופציה לעוד אנשים להצטרף)
            keyboard = [
                [InlineKeyboardButton("גם אני רוצה! 🙋‍♂️", callback_data='join_game')],
                [InlineKeyboardButton("כולם פה, אפשר להתחיל! 🚀", callback_data='start_ai_story')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # עריכת ההודעה הקיימת במקום לשלוח חדשה
            await query.edit_message_text(
                f"🎮 **רשימת שחקנים מעודכנת:**\n{players_list}\n\n"
                f"מחכים שכולם יירשמו... כשתהיו מוכנים, לחצו על הכפתור למטה!",
                reply_markup=reply_markup
            )

        # 2. לחיצה על "התחלנו" - הרגע שבו נועלים את ההרשמה
        elif query.data == 'start_ai_story':
            # בדיקה שיש לפחות שחקן אחד
            if not context.chat_data.get('players'):
                await query.answer("אי אפשר לצאת להרפתקה לבד! חכה שמישהו יצטרף. 😊", show_alert=True)
                return

            # --- הצעד החשוב ביותר ---
            # משנים את המצב ל'פעיל' כדי שאי אפשר יהיה להפעיל שוב את start_game
            context.chat_data['game_active'] = True
            
            await query.edit_message_text("🎲 המערכת בונה את עולם המשחק... הכינו את החרבות! ⚔️")
            
            # כאן נחבר את ה-Logic Engine בשלב הבא
            # story_start = await self.logic_engine.generate_opening(context.chat_data['players'])
            # await query.message.reply_text(story_start)

        # 3. התעלמות מהודעת הברוך הבא
        elif query.data == 'ignore_welcome':
            await query.edit_message_text("אולי פעם אחרת! המשך יום נעים. 😊")
    async def handle_any_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # כאן תבוא הלוגיקה של ה-AI בעתיד
        pass

    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """מסיימת את המשחק ומשחררת את הנעילה"""
        # בדיקה אם בכלל יש משחק פעיל
        if not context.chat_data.get('game_active'):
            await update.message.reply_text("אין משחק פעיל כרגע שאפשר לסיים! 😊")
            return

        # שינוי המצב בחזרה ל-False
        context.chat_data['game_active'] = False
        context.chat_data['players'] = {} # ניקוי רשימת השחקנים
        
        await update.message.reply_text(
            "🏆 **המשחק הסתיים!**\n"
            "מקווים שנהניתם. עכשיו אפשר להתחיל הרפתקה חדשה עם פקודת /start_game."
        )