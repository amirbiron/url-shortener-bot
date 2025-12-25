"""
URL Shortener Bot - Configuration
==================================
כל ההגדרות והקונפיגורציה של הבוט והשרת
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """הגדרות כלליות למערכת"""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # e.g., https://yourapp.onrender.com
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI')
    DB_NAME = os.getenv('DB_NAME', 'url_shortener')
    
    # Web Server (Quart)
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # URL Shortener Settings
    SHORT_CODE_LENGTH = int(os.getenv('SHORT_CODE_LENGTH', 6))
    BASE_URL = os.getenv('BASE_URL', 'https://yourapp.onrender.com')
    
    # Rate Limiting (קישורים לשעה למשתמש)
    MAX_URLS_PER_HOUR = int(os.getenv('MAX_URLS_PER_HOUR', 10))
    MAX_URLS_PER_DAY = int(os.getenv('MAX_URLS_PER_DAY', 50))
    
    # QR Code Settings
    QR_BOX_SIZE = int(os.getenv('QR_BOX_SIZE', 10))
    QR_BORDER = int(os.getenv('QR_BORDER', 4))
    
    # Validation
    MAX_URL_LENGTH = int(os.getenv('MAX_URL_LENGTH', 2048))
    BLOCKED_DOMAINS = os.getenv('BLOCKED_DOMAINS', '').split(',')
    
    @classmethod
    def validate(cls):
        """בדיקת תקינות ההגדרות"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if not cls.MONGODB_URI:
            errors.append("MONGODB_URI is required")
        
        if not cls.WEBHOOK_URL and not cls.DEBUG:
            errors.append("WEBHOOK_URL is required in production")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


class Messages:
    """הודעות הבוט בעברית"""
    
    # הודעות כלליות
    START = """
🎉 **ברוך הבא לבוט קיצור הקישורים!**

אני יכול לעזור לך:
• 🔗 לקצר קישורים ארוכים
• 📊 לעקוב אחרי סטטיסטיקות
• 🖼️ ליצור QR codes
• 📝 לנהל את הקישורים שלך

בחר פעולה מהתפריט למטה 👇
    """
    
    HELP = """
❓ **עזרה - איך להשתמש בבוט**

**פקודות זמינות:**
• `/start` - תפריט ראשי
• `/shorten` - קצר קישור חדש
• `/mylinks` - הקישורים שלי
• `/stats` - סטטיסטיקות כלליות

**איך לקצר קישור:**
1. לחץ על "🔗 קצר קישור חדש"
2. שלח את הקישור הארוך
3. קבל קישור קצר מיידית!

**טיפים:**
• הקישור הקצר יישאר תמיד פעיל
• אתה יכול לעקוב אחרי כמות הקליקים
• ניתן ליצור QR code לכל קישור
    """
    
    # הודעות פעולות
    SEND_URL = """
📎 **שלח לי קישור לקיצור**

פשוט העתק והדבק את הקישור הארוך כאן.

דוגמה:
`https://www.example.com/very/long/url/here`

💡 הקישור חייב להתחיל ב-http:// או https://
    """
    
    URL_SHORTENED = """
✅ **הקישור קוצר בהצלחה!**

🔗 **קישור מקורי:**
{original_url}

🎯 **קישור קצר:**
{short_url}

📊 **קוד:** `{short_code}`
📅 **נוצר:** {created_at}

בחר פעולה מהכפתורים למטה 👇
    """
    
    STATS_MESSAGE = """
📊 **סטטיסטיקות הקישור**

🔗 **קוד:** `{short_code}`
👆 **קליקים:** {clicks}
📅 **נוצר:** {created_at}
🕐 **קליק אחרון:** {last_clicked}

━━━━━━━━━━━━━━━━━━━━━━

🎯 **קישור קצר:**
{short_url}
    """
    
    MY_LINKS_EMPTY = """
📝 **אין לך קישורים עדיין**

לחץ על "🔗 קצר קישור חדש" כדי ליצור את הקישור הראשון שלך!
    """
    
    MY_LINKS_HEADER = """
📝 **הקישורים שלך**

סה"כ: {total} קישורים
עמוד {page}/{total_pages}

━━━━━━━━━━━━━━━━━━━━━━
    """
    
    USER_STATS = """
📊 **הסטטיסטיקות שלך**

🔗 **סה"כ קישורים:** {total_urls}
👆 **סה"כ קליקים:** {total_clicks}
📅 **משתמש מאז:** {member_since}

🏆 **הקישור הפופולרי ביותר:**
{top_url}
({top_clicks} קליקים)
    """
    
    # הודעות שגיאה
    ERROR_INVALID_URL = """
❌ **זה לא נראה כמו קישור תקין**

וודא שהקישור:
• מתחיל ב-http:// או https://
• אינו מכיל רווחים
• הוא כתובת אתר אמיתית

נסה שוב! 🔄
    """
    
    ERROR_URL_TOO_LONG = """
❌ **הקישור ארוך מדי**

אורך מקסימלי: {max_length} תווים
האורך שלך: {current_length} תווים

נסה קישור קצר יותר 🙏
    """
    
    ERROR_BLOCKED_DOMAIN = """
❌ **דומיין חסום**

הדומיין הזה נחסם במערכת מסיבות אבטחה.

אם אתה חושב שזו שגיאה, צור קשר עם התמיכה.
    """
    
    ERROR_RATE_LIMIT = """
⏰ **הגעת למגבלה**

אתה יכול ליצור עד {max_urls} קישורים לשעה.

נסה שוב בעוד {wait_time} דקות.
    """
    
    ERROR_GENERAL = """
❌ **אופס! משהו השתבש**

נסה שוב בעוד כמה רגעים.

אם הבעיה נמשכת, צור קשר עם התמיכה.
    """
    
    ERROR_NOT_FOUND = """
❌ **הקישור לא נמצא**

ייתכן שהקוד שגוי או שהקישור נמחק.
    """
    
    # הודעות מחיקה
    CONFIRM_DELETE = """
⚠️ **האם למחוק את הקישור?**

🔗 {short_url}

**שים לב:** פעולה זו אינה ניתנת לביטול!
    """
    
    DELETED_SUCCESS = """
✅ **הקישור נמחק בהצלחה**

הקישור הקצר כבר לא פעיל.
    """
    
    # הודעות QR
    QR_GENERATED = """
🖼️ **QR Code נוצר בהצלחה!**

סרוק את הקוד כדי לפתוח את הקישור.
    """


class Keyboards:
    """תבניות למקלדות Inline"""
    
    # אייקונים
    ICON_SHORTEN = "🔗"
    ICON_LINK = "🔗"
    ICON_MY_LINKS = "📝"
    ICON_STATS = "📊"
    ICON_HELP = "❓"
    ICON_COPY = "📋"
    ICON_QR = "🖼️"
    ICON_DELETE = "🗑️"
    ICON_BACK = "🔙"
    ICON_NEXT = "▶️"
    ICON_PREV = "◀️"
    ICON_VIEW = "👁️"


class Emojis:
    """אמוג'ים נפוצים"""
    
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LINK = "🔗"
    STATS = "📊"
    CALENDAR = "📅"
    CLOCK = "🕐"
    FIRE = "🔥"
    TROPHY = "🏆"
    LOADING = "⏳"
