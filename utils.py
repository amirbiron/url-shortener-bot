"""
URL Shortener Bot - Utilities
==============================
פונקציות עזר: Base62, QR Codes, Validations, וכו'
"""

import string
import random
import validators
import qrcode
import io
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import Optional, Tuple
from config import Config


class URLShortener:
    """מחלקה לקיצור URLs"""
    
    # תווים ל-Base62 (אותיות גדולות/קטנות + ספרות)
    ALPHABET = string.ascii_letters + string.digits  # 62 תווים
    
    @classmethod
    def generate_short_code(cls, length: int = None) -> str:
        """
        יצירת קוד קצר רנדומלי בסגנון Base62
        
        Args:
            length: אורך הקוד (ברירת מחדל מ-Config)
            
        Returns:
            קוד קצר (למשל: 'dQw4w9')
        """
        if length is None:
            length = Config.SHORT_CODE_LENGTH
        
        return ''.join(random.choice(cls.ALPHABET) for _ in range(length))
    
    @classmethod
    def encode_number(cls, num: int) -> str:
        """
        קידוד מספר ל-Base62
        שימושי אם רוצים קודים sequential במקום random
        
        Args:
            num: מספר לקידוד
            
        Returns:
            מחרוזת Base62
        """
        if num == 0:
            return cls.ALPHABET[0]
        
        result = ''
        while num > 0:
            result = cls.ALPHABET[num % 62] + result
            num //= 62
        
        return result
    
    @classmethod
    def decode_number(cls, code: str) -> int:
        """
        פענוח Base62 למספר
        
        Args:
            code: מחרוזת Base62
            
        Returns:
            המספר המקורי
        """
        num = 0
        for char in code:
            num = num * 62 + cls.ALPHABET.index(char)
        return num


class URLValidator:
    """מחלקה לאימות URLs"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        בדיקה אם URL תקין
        
        Args:
            url: הכתובת לבדיקה
            
        Returns:
            True אם תקין, False אחרת
        """
        # בדיקה בסיסית עם validators
        if not validators.url(url):
            return False
        
        # בדיקה שמתחיל ב-http/https
        if not url.startswith(('http://', 'https://')):
            return False
        
        return True
    
    @staticmethod
    def is_safe_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        בדיקת אבטחה של URL
        
        Args:
            url: הכתובת לבדיקה
            
        Returns:
            (is_safe, reason): (האם בטוח, סיבה אם לא)
        """
        # בדיקת תקינות בסיסית
        if not URLValidator.is_valid_url(url):
            return False, "invalid_url"
        
        # בדיקת אורך
        if len(url) > Config.MAX_URL_LENGTH:
            return False, "url_too_long"
        
        # בדיקת דומיינים חסומים
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for blocked in Config.BLOCKED_DOMAINS:
                if blocked and blocked.lower() in domain:
                    return False, "blocked_domain"
        except Exception:
            return False, "parse_error"
        
        return True, None
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        נרמול URL (הסרת רווחים, lowercase של דומיין)
        
        Args:
            url: הכתובת המקורית
            
        Returns:
            URL מנורמל
        """
        url = url.strip()
        
        # אם לא מתחיל ב-http, נוסיף https
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url


class QRCodeGenerator:
    """מחלקה ליצירת QR Codes"""
    
    @staticmethod
    def generate(url: str, logo_path: Optional[str] = None) -> io.BytesIO:
        """
        יצירת QR Code עבור URL
        
        Args:
            url: הכתובת ליצירת QR
            logo_path: נתיב ללוגו (אופציונלי)
            
        Returns:
            BytesIO עם תמונת ה-QR
        """
        # יצירת QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=Config.QR_BOX_SIZE,
            border=Config.QR_BORDER,
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        # יצירת התמונה
        img = qr.make_image(fill_color="black", back_color="white")
        
        # TODO: הוספת לוגו אם נדרש (Phase 2)
        # if logo_path:
        #     logo = Image.open(logo_path)
        #     ...
        
        # המרה ל-BytesIO
        byte_io = io.BytesIO()
        img.save(byte_io, format='PNG')
        byte_io.seek(0)
        
        return byte_io


class RateLimiter:
    """מחלקה לניהול Rate Limiting (בזיכרון)"""
    
    def __init__(self):
        # מבנה: {user_id: [timestamp1, timestamp2, ...]}
        self._user_requests = {}
    
    def check_limit(self, user_id: int) -> Tuple[bool, Optional[int]]:
        """
        בדיקה אם המשתמש הגיע למגבלה
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            (can_proceed, wait_minutes): (האם יכול להמשיך, דקות המתנה)
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # אתחול אם משתמש חדש
        if user_id not in self._user_requests:
            self._user_requests[user_id] = []
        
        # ניקוי בקשות ישנות
        self._user_requests[user_id] = [
            ts for ts in self._user_requests[user_id]
            if ts > hour_ago
        ]
        
        # בדיקת מגבלה
        request_count = len(self._user_requests[user_id])
        
        if request_count >= Config.MAX_URLS_PER_HOUR:
            # חישוב זמן המתנה
            oldest_request = min(self._user_requests[user_id])
            wait_until = oldest_request + timedelta(hours=1)
            wait_minutes = int((wait_until - now).total_seconds() / 60) + 1
            
            return False, wait_minutes
        
        return True, None
    
    def add_request(self, user_id: int):
        """
        הוספת בקשה לרשימה
        
        Args:
            user_id: מזהה המשתמש
        """
        now = datetime.utcnow()
        
        if user_id not in self._user_requests:
            self._user_requests[user_id] = []
        
        self._user_requests[user_id].append(now)
    
    def cleanup(self):
        """ניקוי תקופתי של נתונים ישנים"""
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        for user_id in list(self._user_requests.keys()):
            self._user_requests[user_id] = [
                ts for ts in self._user_requests[user_id]
                if ts > hour_ago
            ]
            
            # מחיקת משתמשים ללא בקשות אחרונות
            if not self._user_requests[user_id]:
                del self._user_requests[user_id]


class DateFormatter:
    """מחלקה לעיצוב תאריכים בעברית"""
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        עיצוב תאריך ושעה בפורמט קריא
        
        Args:
            dt: אובייקט datetime
            
        Returns:
            מחרוזת מעוצבת (למשל: "24/12/2024 15:30")
        """
        return dt.strftime('%d/%m/%Y %H:%M')
    
    @staticmethod
    def format_date(dt: datetime) -> str:
        """
        עיצוב תאריך בלבד
        
        Args:
            dt: אובייקט datetime
            
        Returns:
            מחרוזת מעוצבת (למשל: "24/12/2024")
        """
        return dt.strftime('%d/%m/%Y')
    
    @staticmethod
    def time_ago(dt: datetime) -> str:
        """
        חישוב "לפני כמה זמן" בעברית
        
        Args:
            dt: אובייקט datetime
            
        Returns:
            מחרוזת מעוצבת (למשל: "לפני 3 שעות")
        """
        now = datetime.utcnow()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "לפני רגע"
        
        minutes = int(seconds / 60)
        if minutes < 60:
            return f"לפני {minutes} דקות" if minutes > 1 else "לפני דקה"
        
        hours = int(minutes / 60)
        if hours < 24:
            return f"לפני {hours} שעות" if hours > 1 else "לפני שעה"
        
        days = int(hours / 24)
        if days < 30:
            return f"לפני {days} ימים" if days > 1 else "אתמול"
        
        months = int(days / 30)
        if months < 12:
            return f"לפני {months} חודשים" if months > 1 else "לפני חודש"
        
        years = int(months / 12)
        return f"לפני {years} שנים" if years > 1 else "לפני שנה"


class StatisticsCalculator:
    """מחלקה לחישובי סטטיסטיקות"""
    
    @staticmethod
    def calculate_click_rate(clicks: int, days_old: int) -> float:
        """
        חישוב ממוצע קליקים ליום
        
        Args:
            clicks: מספר קליקים
            days_old: גיל הקישור בימים
            
        Returns:
            ממוצע קליקים ליום
        """
        if days_old == 0:
            days_old = 1
        
        return round(clicks / days_old, 2)
    
    @staticmethod
    def format_large_number(num: int) -> str:
        """
        עיצוב מספר גדול בפורמט קריא
        
        Args:
            num: המספר לעיצוב
            
        Returns:
            מחרוזת מעוצבת (למשל: "1.2K", "3.5M")
        """
        if num < 1000:
            return str(num)
        
        if num < 1_000_000:
            return f"{num/1000:.1f}K"
        
        if num < 1_000_000_000:
            return f"{num/1_000_000:.1f}M"
        
        return f"{num/1_000_000_000:.1f}B"


class TextFormatter:
    """מחלקה לעיצוב טקסטים"""
    
    @staticmethod
    def truncate(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """
        קיצור טקסט עם סיומת
        
        Args:
            text: הטקסט לקיצור
            max_length: אורך מקסימלי
            suffix: סיומת (ברירת מחדל: "...")
            
        Returns:
            טקסט מקוצר
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        escape של תווים מיוחדים ב-Markdown
        
        Args:
            text: הטקסט המקורי
            
        Returns:
            טקסט מ-escaped
        """
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 10) -> str:
        """
        יצירת progress bar טקסטואלי
        
        Args:
            current: ערך נוכחי
            total: ערך מקסימלי
            length: אורך ה-bar
            
        Returns:
            progress bar (למשל: "████░░░░░░ 40%")
        """
        if total == 0:
            percentage = 0
        else:
            percentage = int((current / total) * 100)
        
        filled = int((current / total) * length) if total > 0 else 0
        empty = length - filled
        
        bar = "█" * filled + "░" * empty
        
        return f"{bar} {percentage}%"


# Singleton instances
rate_limiter = RateLimiter()


# Helper functions (shortcuts)
def generate_short_code(length: int = None) -> str:
    """Shortcut for URLShortener.generate_short_code()"""
    return URLShortener.generate_short_code(length)


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Shortcut for URLValidator.is_safe_url()"""
    return URLValidator.is_safe_url(url)


def generate_qr(url: str) -> io.BytesIO:
    """Shortcut for QRCodeGenerator.generate()"""
    return QRCodeGenerator.generate(url)


def format_time_ago(dt: datetime) -> str:
    """Shortcut for DateFormatter.time_ago()"""
    return DateFormatter.time_ago(dt)


def truncate_text(text: str, max_length: int = 50) -> str:
    """Shortcut for TextFormatter.truncate()"""
    return TextFormatter.truncate(text, max_length)
