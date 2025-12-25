"""
URL Shortener Bot - Database Layer
===================================
כל הפעולות על MongoDB: יצירה, קריאה, עדכון, מחיקה
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import Config
import logging

logger = logging.getLogger(__name__)


class Database:
    """מחלקה לניהול MongoDB"""
    
    def __init__(self):
        """אתחול חיבור ל-MongoDB"""
        try:
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            
            # בדיקת חיבור
            self.client.server_info()
            
            self.db = self.client[Config.DB_NAME]
            
            # Collections
            self.urls = self.db.urls
            self.users = self.db.users
            self.clicks = self.db.clicks
            
            # יצירת אינדקסים
            self._create_indexes()
            
            logger.info("✅ Connected to MongoDB successfully")
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """יצירת אינדקסים לביצועים טובים"""
        try:
            # אינדקס unique על short_code
            self.urls.create_index([("short_code", ASCENDING)], unique=True)
            
            # אינדקס על user_id למשיכה מהירה
            self.urls.create_index([("user_id", ASCENDING)])
            
            # אינדקס על created_at למיון
            self.urls.create_index([("created_at", DESCENDING)])
            
            # אינדקס compound למשיכת URLs של משתמש ספציפי
            self.urls.create_index([
                ("user_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            
            # אינדקס על users
            self.users.create_index([("user_id", ASCENDING)], unique=True)
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    def close(self):
        """סגירת חיבור ל-MongoDB"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


class URLRepository:
    """מחלקה לניהול URLs במסד הנתונים"""
    
    def __init__(self, db: Database):
        self.collection = db.urls
    
    def create(
        self,
        user_id: int,
        original_url: str,
        short_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        יצירת URL חדש
        
        Args:
            user_id: מזהה המשתמש
            original_url: הכתובת המקורית
            short_code: הקוד הקצר
            
        Returns:
            המסמך שנוצר או None אם נכשל
        """
        try:
            doc = {
                "user_id": user_id,
                "original_url": original_url,
                "short_code": short_code,
                "created_at": datetime.utcnow(),
                "clicks": 0,
                "last_clicked": None
            }
            
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            
            logger.info(f"✅ Created URL: {short_code} for user {user_id}")
            return doc
            
        except DuplicateKeyError:
            logger.warning(f"⚠️ Duplicate short_code: {short_code}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating URL: {e}")
            return None
    
    def get_by_short_code(self, short_code: str) -> Optional[Dict[str, Any]]:
        """
        משיכת URL לפי קוד קצר
        
        Args:
            short_code: הקוד הקצר
            
        Returns:
            המסמך או None אם לא נמצא
        """
        try:
            return self.collection.find_one({"short_code": short_code})
        except Exception as e:
            logger.error(f"❌ Error getting URL by code: {e}")
            return None
    
    def get_by_id(self, url_id: str) -> Optional[Dict[str, Any]]:
        """
        משיכת URL לפי ID
        
        Args:
            url_id: מזהה המסמך
            
        Returns:
            המסמך או None אם לא נמצא
        """
        try:
            from bson import ObjectId
            return self.collection.find_one({"_id": ObjectId(url_id)})
        except Exception as e:
            logger.error(f"❌ Error getting URL by ID: {e}")
            return None
    
    def find_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        משיכת כל ה-URLs של משתמש עם pagination
        
        Args:
            user_id: מזהה המשתמש
            skip: כמה לדלג (לפגינציה)
            limit: כמה להחזיר
            
        Returns:
            רשימת מסמכים
        """
        try:
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort(
                "created_at", DESCENDING
            ).skip(skip).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"❌ Error finding URLs by user: {e}")
            return []
    
    def count_by_user(self, user_id: int) -> int:
        """
        ספירת כמות ה-URLs של משתמש
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            מספר ה-URLs
        """
        try:
            return self.collection.count_documents({"user_id": user_id})
        except Exception as e:
            logger.error(f"❌ Error counting URLs: {e}")
            return 0
    
    def increment_clicks(self, short_code: str) -> bool:
        """
        הגדלת מונה הקליקים
        
        Args:
            short_code: הקוד הקצר
            
        Returns:
            True אם הצליח, False אחרת
        """
        try:
            result = self.collection.update_one(
                {"short_code": short_code},
                {
                    "$inc": {"clicks": 1},
                    "$set": {"last_clicked": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error incrementing clicks: {e}")
            return False
    
    def delete(self, short_code: str, user_id: int) -> bool:
        """
        מחיקת URL
        
        Args:
            short_code: הקוד הקצר
            user_id: מזהה המשתמש (לאימות בעלות)
            
        Returns:
            True אם נמחק, False אחרת
        """
        try:
            result = self.collection.delete_one({
                "short_code": short_code,
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted URL: {short_code}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting URL: {e}")
            return False
    
    def find_existing(self, user_id: int, original_url: str) -> Optional[Dict[str, Any]]:
        """
        חיפוש אם המשתמש כבר קיצר את אותו URL
        
        Args:
            user_id: מזהה המשתמש
            original_url: הכתובת המקורית
            
        Returns:
            המסמך או None אם לא נמצא
        """
        try:
            return self.collection.find_one({
                "user_id": user_id,
                "original_url": original_url
            })
        except Exception as e:
            logger.error(f"❌ Error finding existing URL: {e}")
            return None
    
    def get_top_urls(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        משיכת ה-URLs הכי פופולריים של משתמש
        
        Args:
            user_id: מזהה המשתמש
            limit: כמה להחזיר
            
        Returns:
            רשימת URLs ממוינת לפי קליקים
        """
        try:
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort(
                "clicks", DESCENDING
            ).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"❌ Error getting top URLs: {e}")
            return []
    
    def get_total_clicks(self, user_id: int) -> int:
        """
        סכימת כל הקליקים של משתמש
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            סה"כ קליקים
        """
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": None, "total": {"$sum": "$clicks"}}}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if result:
                return result[0]["total"]
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error calculating total clicks: {e}")
            return 0


class UserRepository:
    """מחלקה לניהול משתמשים במסד הנתונים"""
    
    def __init__(self, db: Database):
        self.collection = db.users
    
    def create_or_update(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        יצירת משתמש חדש או עדכון קיים
        
        Args:
            user_id: מזהה המשתמש
            username: שם משתמש (אופציונלי)
            first_name: שם פרטי (אופציונלי)
            last_name: שם משפחה (אופציונלי)
            
        Returns:
            המסמך המעודכן
        """
        try:
            now = datetime.utcnow()
            
            result = self.collection.find_one_and_update(
                {"user_id": user_id},
                {
                    "$set": {
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                        "last_seen": now
                    },
                    "$setOnInsert": {
                        "created_at": now
                    }
                },
                upsert=True,
                return_document=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error creating/updating user: {e}")
            return None
    
    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        משיכת פרטי משתמש
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            המסמך או None אם לא נמצא
        """
        try:
            return self.collection.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None
    
    def update_last_seen(self, user_id: int) -> bool:
        """
        עדכון זמן ביקור אחרון
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            True אם הצליח, False אחרת
        """
        try:
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_seen": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating last seen: {e}")
            return False
    
    def get_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        משיכת סטטיסטיקות משתמש
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            dict עם סטטיסטיקות
        """
        try:
            user = self.get(user_id)
            if not user:
                return None
            
            # יבוא זמני של URLRepository
            from database import db
            url_repo = URLRepository(db)
            
            total_urls = url_repo.count_by_user(user_id)
            total_clicks = url_repo.get_total_clicks(user_id)
            top_urls = url_repo.get_top_urls(user_id, limit=1)
            
            return {
                "user_id": user_id,
                "member_since": user.get("created_at"),
                "total_urls": total_urls,
                "total_clicks": total_clicks,
                "top_url": top_urls[0] if top_urls else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return None


# Singleton instance
db = Database()
url_repo = URLRepository(db)
user_repo = UserRepository(db)


# Helper functions (shortcuts)
def create_url(user_id: int, original_url: str, short_code: str) -> Optional[Dict]:
    """Shortcut for url_repo.create()"""
    return url_repo.create(user_id, original_url, short_code)


def get_url(short_code: str) -> Optional[Dict]:
    """Shortcut for url_repo.get_by_short_code()"""
    return url_repo.get_by_short_code(short_code)


def increment_clicks(short_code: str) -> bool:
    """Shortcut for url_repo.increment_clicks()"""
    return url_repo.increment_clicks(short_code)


def get_user_urls(user_id: int, page: int = 1, per_page: int = 10) -> List[Dict]:
    """Shortcut for url_repo.find_by_user() with page calculation"""
    skip = (page - 1) * per_page
    return url_repo.find_by_user(user_id, skip=skip, limit=per_page)


def count_user_urls(user_id: int) -> int:
    """Shortcut for url_repo.count_by_user()"""
    return url_repo.count_by_user(user_id)


def create_or_update_user(user_id: int, **kwargs) -> Optional[Dict]:
    """Shortcut for user_repo.create_or_update()"""
    return user_repo.create_or_update(user_id, **kwargs)


def get_user_stats(user_id: int) -> Optional[Dict]:
    """Shortcut for user_repo.get_stats()"""
    return user_repo.get_stats(user_id)
