"""
URL Shortener Bot - Main Bot Logic
===================================
כל ההנדלרים והלוגיקה של הבוט
"""

import logging
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from config import Config, Messages
from database import (
    url_repo,
    user_repo,
    create_url,
    get_url,
    get_user_urls,
    count_user_urls,
    create_or_update_user,
    get_user_stats
)
from utils import (
    generate_short_code,
    validate_url,
    generate_qr,
    format_time_ago,
    truncate_text,
    rate_limiter,
    URLValidator,
    DateFormatter
)
from keyboards import (
    main_menu_keyboard,
    url_actions_keyboard,
    stats_keyboard,
    pagination_keyboard,
    delete_confirm_keyboard,
    qr_keyboard,
    back_keyboard,
    user_stats_keyboard
)
import math

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotHandlers:
    """מחלקה המכילה את כל ה-handlers של הבוט"""
    
    def __init__(self):
        # מצב המשתמש (לשמירת context בין הודעות)
        self.user_states = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        פקודת /start - הודעת פתיחה
        """
        user = update.effective_user
        
        # שמירת פרטי המשתמש ב-DB
        create_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        await update.message.reply_text(
            Messages.START,
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"User {user.id} (@{user.username}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        פקודת /help - עזרה
        """
        await update.message.reply_text(
            Messages.HELP,
            reply_markup=back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def shorten_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        פקודת /shorten - קיצור קישור
        """
        user_id = update.effective_user.id
        
        # בדיקת rate limiting
        can_proceed, wait_minutes = rate_limiter.check_limit(user_id)
        
        if not can_proceed:
            await update.message.reply_text(
                Messages.ERROR_RATE_LIMIT.format(
                    max_urls=Config.MAX_URLS_PER_HOUR,
                    wait_time=wait_minutes
                ),
                reply_markup=back_keyboard()
            )
            return
        
        # הגדרת מצב המתנה ל-URL
        self.user_states[user_id] = 'waiting_for_url'
        
        await update.message.reply_text(
            Messages.SEND_URL,
            reply_markup=back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def mylinks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        פקודת /mylinks - הצגת קישורים של המשתמש
        """
        user_id = update.effective_user.id
        
        await self._show_my_links(update, context, user_id, page=1)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        פקודת /stats - סטטיסטיקות משתמש
        """
        user_id = update.effective_user.id
        
        await self._show_user_stats(update, context, user_id)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        טיפול בלחיצות על כפתורים
        """
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        logger.info(f"User {user_id} clicked button: {data}")
        
        # ניתוב לפי סוג הכפתור
        if data == 'main_menu':
            await self._handle_main_menu(query, context)
        
        elif data == 'shorten_new':
            await self._handle_shorten_new(query, context, user_id)
        
        elif data == 'my_links':
            await self._handle_my_links(query, context, user_id)
        
        elif data == 'user_stats':
            await self._handle_user_stats_button(query, context, user_id)
        
        elif data == 'help':
            await self._handle_help(query, context)
        
        elif data.startswith('view_'):
            short_code = data.replace('view_', '')
            await self._handle_view_url(query, context, short_code)
        
        elif data.startswith('stats_'):
            short_code = data.replace('stats_', '')
            await self._handle_stats(query, context, short_code)
        
        elif data.startswith('qr_'):
            short_code = data.replace('qr_', '')
            await self._handle_qr(query, context, short_code, user_id)
        
        elif data.startswith('delete_confirm_'):
            short_code = data.replace('delete_confirm_', '')
            await self._handle_delete_confirm(query, context, short_code)
        
        elif data.startswith('delete_confirmed_'):
            short_code = data.replace('delete_confirmed_', '')
            await self._handle_delete_confirmed(query, context, short_code, user_id)
        
        elif data.startswith('page_'):
            page = int(data.replace('page_', ''))
            await self._handle_pagination(query, context, user_id, page)
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        טיפול בהודעות טקסט (בעיקר URLs)
        """
        user_id = update.effective_user.id
        text = update.message.text
        
        # בדיקה אם המשתמש במצב המתנה ל-URL
        if self.user_states.get(user_id) == 'waiting_for_url':
            await self._process_url_shortening(update, context, user_id, text)
            # איפוס המצב
            self.user_states[user_id] = None
        else:
            # הודעה כללית
            await update.message.reply_text(
                "לא הבנתי 🤔\n\nלחץ על /start לתפריט הראשי",
                reply_markup=back_keyboard()
            )
    
    # ==================== Helper Methods ====================
    
    async def _show_my_links(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        page: int = 1
    ):
        """הצגת רשימת קישורים של המשתמש"""
        # ספירת סה"כ קישורים
        total_urls = count_user_urls(user_id)
        
        if total_urls == 0:
            message = Messages.MY_LINKS_EMPTY
            keyboard = main_menu_keyboard()
        else:
            # חישוב pagination
            per_page = 5
            total_pages = math.ceil(total_urls / per_page)
            
            # משיכת קישורים לעמוד הנוכחי
            urls = get_user_urls(user_id, page=page, per_page=per_page)
            
            # בניית הודעה
            message = Messages.MY_LINKS_HEADER.format(
                total=total_urls,
                page=page,
                total_pages=total_pages
            )
            
            keyboard = pagination_keyboard(urls, page, total_pages, user_id)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=keyboard
            )
    
    async def _show_user_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int
    ):
        """הצגת סטטיסטיקות המשתמש"""
        stats = get_user_stats(user_id)
        
        if not stats:
            message = "❌ לא נמצאו נתונים"
            keyboard = back_keyboard()
        else:
            # עיצוב הודעת הסטטיסטיקות
            member_since = DateFormatter.format_date(stats['member_since'])
            
            top_url_text = "אין עדיין"
            if stats['top_url']:
                top = stats['top_url']
                top_url_text = f"{truncate_text(top['original_url'], 40)}\n`{Config.BASE_URL}/{top['short_code']}`"
                top_clicks = top.get('clicks', 0)
            else:
                top_clicks = 0
            
            message = Messages.USER_STATS.format(
                total_urls=stats['total_urls'],
                total_clicks=stats['total_clicks'],
                member_since=member_since,
                top_url=top_url_text,
                top_clicks=top_clicks
            )
            
            keyboard = user_stats_keyboard()
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _process_url_shortening(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        url: str
    ):
        """עיבוד קיצור URL"""
        
        # נרמול ה-URL
        url = URLValidator.normalize_url(url)
        
        # בדיקת תקינות ואבטחה
        is_safe, reason = validate_url(url)
        
        if not is_safe:
            # הודעת שגיאה מתאימה
            if reason == 'invalid_url':
                message = Messages.ERROR_INVALID_URL
            elif reason == 'url_too_long':
                message = Messages.ERROR_URL_TOO_LONG.format(
                    max_length=Config.MAX_URL_LENGTH,
                    current_length=len(url)
                )
            elif reason == 'blocked_domain':
                message = Messages.ERROR_BLOCKED_DOMAIN
            else:
                message = Messages.ERROR_GENERAL
            
            await update.message.reply_text(
                message,
                reply_markup=back_keyboard()
            )
            return
        
        # בדיקה אם המשתמש כבר קיצר את הקישור הזה
        existing = url_repo.find_existing(user_id, url)
        
        if existing:
            # הקישור כבר קיים - פשוט נחזיר אותו
            short_code = existing['short_code']
            short_url = f"{Config.BASE_URL}/{short_code}"
            created_at = DateFormatter.format_datetime(existing['created_at'])
            
            message = "♻️ **קיצרת את הקישור הזה בעבר!**\n\n" + \
                     Messages.URL_SHORTENED.format(
                         original_url=truncate_text(url, 100),
                         short_url=short_url,
                         short_code=short_code,
                         created_at=created_at
                     )
        else:
            # יצירת קוד קצר חדש
            max_attempts = 5
            short_code = None
            
            for _ in range(max_attempts):
                temp_code = generate_short_code()
                
                # בדיקה שהקוד לא קיים
                if not get_url(temp_code):
                    short_code = temp_code
                    break
            
            if not short_code:
                await update.message.reply_text(
                    Messages.ERROR_GENERAL,
                    reply_markup=back_keyboard()
                )
                return
            
            # שמירה ב-DB
            url_doc = create_url(user_id, url, short_code)
            
            if not url_doc:
                await update.message.reply_text(
                    Messages.ERROR_GENERAL,
                    reply_markup=back_keyboard()
                )
                return
            
            # הוספה ל-rate limiter
            rate_limiter.add_request(user_id)
            
            # בניית ההודעה
            short_url = f"{Config.BASE_URL}/{short_code}"
            created_at = DateFormatter.format_datetime(url_doc['created_at'])
            
            message = Messages.URL_SHORTENED.format(
                original_url=truncate_text(url, 100),
                short_url=short_url,
                short_code=short_code,
                created_at=created_at
            )
            
            logger.info(f"Created short URL: {short_code} for user {user_id}")
        
        # שליחת התשובה
        keyboard = url_actions_keyboard(short_code, short_url)
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ==================== Button Handlers ====================
    
    async def _handle_main_menu(self, query, context):
        """טיפול בכפתור תפריט ראשי"""
        await query.edit_message_text(
            Messages.START,
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_shorten_new(self, query, context, user_id):
        """טיפול בכפתור קיצור חדש"""
        # בדיקת rate limiting
        can_proceed, wait_minutes = rate_limiter.check_limit(user_id)
        
        if not can_proceed:
            await query.edit_message_text(
                Messages.ERROR_RATE_LIMIT.format(
                    max_urls=Config.MAX_URLS_PER_HOUR,
                    wait_time=wait_minutes
                ),
                reply_markup=back_keyboard()
            )
            return
        
        # הגדרת מצב המתנה
        self.user_states[user_id] = 'waiting_for_url'
        
        await query.edit_message_text(
            Messages.SEND_URL,
            reply_markup=back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_my_links(self, query, context, user_id):
        """טיפול בכפתור הקישורים שלי"""
        await self._show_my_links(query, context, user_id, page=1)
    
    async def _handle_user_stats_button(self, query, context, user_id):
        """טיפול בכפתור סטטיסטיקות"""
        await self._show_user_stats(query, context, user_id)
    
    async def _handle_help(self, query, context):
        """טיפול בכפתור עזרה"""
        await query.edit_message_text(
            Messages.HELP,
            reply_markup=back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_view_url(self, query, context, short_code):
        """טיפול בצפייה בקישור"""
        url_doc = get_url(short_code)
        
        if not url_doc:
            await query.edit_message_text(
                Messages.ERROR_NOT_FOUND,
                reply_markup=back_keyboard()
            )
            return
        
        short_url = f"{Config.BASE_URL}/{short_code}"
        created_at = DateFormatter.format_datetime(url_doc['created_at'])
        
        message = Messages.URL_SHORTENED.format(
            original_url=truncate_text(url_doc['original_url'], 100),
            short_url=short_url,
            short_code=short_code,
            created_at=created_at
        )
        
        await query.edit_message_text(
            message,
            reply_markup=url_actions_keyboard(short_code, short_url),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def _handle_stats(self, query, context, short_code):
        """טיפול בצפייה בסטטיסטיקות קישור"""
        url_doc = get_url(short_code)
        
        if not url_doc:
            await query.edit_message_text(
                Messages.ERROR_NOT_FOUND,
                reply_markup=back_keyboard()
            )
            return
        
        # עיצוב הסטטיסטיקות
        short_url = f"{Config.BASE_URL}/{short_code}"
        created_at = DateFormatter.format_datetime(url_doc['created_at'])
        
        last_clicked = "אף פעם"
        if url_doc.get('last_clicked'):
            last_clicked = format_time_ago(url_doc['last_clicked'])
        
        message = Messages.STATS_MESSAGE.format(
            short_code=short_code,
            clicks=url_doc.get('clicks', 0),
            created_at=created_at,
            last_clicked=last_clicked,
            short_url=short_url
        )
        
        await query.edit_message_text(
            message,
            reply_markup=stats_keyboard(short_code),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def _handle_qr(self, query, context, short_code, user_id):
        """טיפול ביצירת QR Code"""
        url_doc = get_url(short_code)
        
        if not url_doc:
            await query.answer("❌ הקישור לא נמצא", show_alert=True)
            return
        
        # בדיקת בעלות (אופציונלי - אפשר להסיר אם רוצים לאפשר לכולם)
        # if url_doc['user_id'] != user_id:
        #     await query.answer("❌ אין לך הרשאה", show_alert=True)
        #     return
        
        try:
            # יצירת QR
            short_url = f"{Config.BASE_URL}/{short_code}"
            qr_image = generate_qr(short_url)
            
            # שליחת התמונה
            await query.message.reply_photo(
                photo=InputFile(qr_image, filename=f'qr_{short_code}.png'),
                caption=Messages.QR_GENERATED,
                reply_markup=qr_keyboard(short_code)
            )
            
            await query.answer("✅ QR Code נוצר!")
            
            logger.info(f"Generated QR for {short_code}")
            
        except Exception as e:
            logger.error(f"Error generating QR: {e}")
            await query.answer("❌ שגיאה ביצירת QR", show_alert=True)
    
    async def _handle_delete_confirm(self, query, context, short_code):
        """טיפול באישור מחיקה"""
        url_doc = get_url(short_code)
        
        if not url_doc:
            await query.answer("❌ הקישור לא נמצא", show_alert=True)
            return
        
        short_url = f"{Config.BASE_URL}/{short_code}"
        
        message = Messages.CONFIRM_DELETE.format(short_url=short_url)
        
        await query.edit_message_text(
            message,
            reply_markup=delete_confirm_keyboard(short_code),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_delete_confirmed(self, query, context, short_code, user_id):
        """טיפול במחיקה מאושרת"""
        # מחיקה מה-DB
        success = url_repo.delete(short_code, user_id)
        
        if success:
            await query.edit_message_text(
                Messages.DELETED_SUCCESS,
                reply_markup=back_keyboard()
            )
            logger.info(f"User {user_id} deleted URL: {short_code}")
        else:
            await query.answer("❌ שגיאה במחיקה", show_alert=True)
    
    async def _handle_pagination(self, query, context, user_id, page):
        """טיפול בניווט בין עמודים"""
        await self._show_my_links(query, context, user_id, page=page)


# ==================== Bot Setup ====================

def create_bot_application() -> Application:
    """
    יצירת אפליקציית הבוט
    
    Returns:
        Application instance
    """
    # בדיקת קונפיגורציה
    Config.validate()
    
    # יצירת Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # יצירת instance של handlers
    handlers = BotHandlers()
    
    # רישום handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("shorten", handlers.shorten_command))
    application.add_handler(CommandHandler("mylinks", handlers.mylinks_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(handlers.button_callback))
    
    # Message handlers (text)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.message_handler)
    )
    
    logger.info("✅ Bot application created successfully")
    
    return application


# ==================== Main Function ====================

async def main():
    """
    פונקציה ראשית להרצת הבוט במצב polling (לפיתוח)
    """
    application = create_bot_application()
    
    logger.info("🚀 Starting bot in polling mode...")
    
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
