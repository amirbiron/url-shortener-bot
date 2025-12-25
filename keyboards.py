"""
URL Shortener Bot - Inline Keyboards
=====================================
כל המקלדות האינליין של הבוט
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional
from config import Keyboards
import math


class KeyboardBuilder:
    """מחלקה לבניית מקלדות אינליין"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """
        תפריט ראשי
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_SHORTEN} קצר קישור חדש",
                    callback_data='shorten_new'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_MY_LINKS} הקישורים שלי",
                    callback_data='my_links'
                ),
                InlineKeyboardButton(
                    f"{Keyboards.ICON_STATS} סטטיסטיקות",
                    callback_data='user_stats'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_HELP} עזרה",
                    callback_data='help'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def url_actions(short_code: str, short_url: str) -> InlineKeyboardMarkup:
        """
        כפתורים לאחר יצירת קישור
        
        Args:
            short_code: הקוד הקצר
            short_url: הכתובת הקצרה המלאה
            
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_COPY} פתח קישור",
                    url=short_url
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_QR} צור QR Code",
                    callback_data=f'qr_{short_code}'
                ),
                InlineKeyboardButton(
                    f"{Keyboards.ICON_STATS} סטטיסטיקות",
                    callback_data=f'stats_{short_code}'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_DELETE} מחק קישור",
                    callback_data=f'delete_confirm_{short_code}'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_BACK} תפריט ראשי",
                    callback_data='main_menu'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def stats_actions(short_code: str) -> InlineKeyboardMarkup:
        """
        כפתורים בתצוגת סטטיסטיקות
        
        Args:
            short_code: הקוד הקצר
            
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_QR} צור QR Code",
                    callback_data=f'qr_{short_code}'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_DELETE} מחק קישור",
                    callback_data=f'delete_confirm_{short_code}'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_BACK} חזור",
                    callback_data='my_links'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def my_links_pagination(
        urls: List[dict],
        page: int,
        total_pages: int,
        user_id: int
    ) -> InlineKeyboardMarkup:
        """
        רשימת קישורים עם pagination
        
        Args:
            urls: רשימת ה-URLs להצגה
            page: עמוד נוכחי
            total_pages: סה"כ עמודים
            user_id: מזהה המשתמש (לא בשימוש כרגע)
            
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = []
        
        # כפתורי קישורים (עד 5 בעמוד)
        for url in urls[:5]:
            short_code = url['short_code']
            clicks = url.get('clicks', 0)
            
            # קיצור ה-URL המקורי להצגה
            from utils import truncate_text
            display_url = truncate_text(url['original_url'], 30)
            
            button_text = f"{Keyboards.ICON_LINK} {display_url} ({clicks} 👆)"
            
            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f'view_{short_code}'
                )
            ])
        
        # כפתורי ניווט
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    f"{Keyboards.ICON_PREV} הקודם",
                    callback_data=f'page_{page-1}'
                )
            )
        
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    f"הבא {Keyboards.ICON_NEXT}",
                    callback_data=f'page_{page+1}'
                )
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # כפתור חזרה
        keyboard.append([
            InlineKeyboardButton(
                f"{Keyboards.ICON_BACK} תפריט ראשי",
                callback_data='main_menu'
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def delete_confirmation(short_code: str) -> InlineKeyboardMarkup:
        """
        אישור מחיקה
        
        Args:
            short_code: הקוד הקצר
            
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ כן, מחק",
                    callback_data=f'delete_confirmed_{short_code}'
                ),
                InlineKeyboardButton(
                    "❌ ביטול",
                    callback_data=f'view_{short_code}'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def qr_actions(short_code: str) -> InlineKeyboardMarkup:
        """
        כפתורים אחרי יצירת QR
        
        Args:
            short_code: הקוד הקצר
            
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_VIEW} צפה בקישור",
                    callback_data=f'view_{short_code}'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_BACK} תפריט ראשי",
                    callback_data='main_menu'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """
        רק כפתור חזרה לתפריט
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_BACK} תפריט ראשי",
                    callback_data='main_menu'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_stats_actions() -> InlineKeyboardMarkup:
        """
        כפתורים בתצוגת סטטיסטיקות משתמש
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_MY_LINKS} הקישורים שלי",
                    callback_data='my_links'
                )
            ],
            [
                InlineKeyboardButton(
                    f"{Keyboards.ICON_BACK} תפריט ראשי",
                    callback_data='main_menu'
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)


# Singleton instance
kb = KeyboardBuilder()


# Helper functions (shortcuts)
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.main_menu()"""
    return kb.main_menu()


def url_actions_keyboard(short_code: str, short_url: str) -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.url_actions()"""
    return kb.url_actions(short_code, short_url)


def stats_keyboard(short_code: str) -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.stats_actions()"""
    return kb.stats_actions(short_code)


def pagination_keyboard(
    urls: List[dict],
    page: int,
    total_pages: int,
    user_id: int
) -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.my_links_pagination()"""
    return kb.my_links_pagination(urls, page, total_pages, user_id)


def delete_confirm_keyboard(short_code: str) -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.delete_confirmation()"""
    return kb.delete_confirmation(short_code)


def qr_keyboard(short_code: str) -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.qr_actions()"""
    return kb.qr_actions(short_code)


def back_keyboard() -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.back_to_menu()"""
    return kb.back_to_menu()


def user_stats_keyboard() -> InlineKeyboardMarkup:
    """Shortcut for KeyboardBuilder.user_stats_actions()"""
    return kb.user_stats_actions()
