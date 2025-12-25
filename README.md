# 🔗 URL Shortener Bot

בוט טלגרם מתקדם לקיצור קישורים עם ניהול מלא, סטטיסטיקות ו-QR codes.

## ✨ פיצ'רים

- ✅ קיצור קישורים ארוכים לקישורים קצרים וידידותיים
- 📊 מעקב אחר כמות קליקים לכל קישור
- 🖼️ יצירת QR Codes עבור קישורים
- 📝 ניהול כל הקישורים שלך במקום אחד
- 🔒 אבטחה: חסימת דומיינים מסוכנים
- ⏰ Rate Limiting למניעת ספאם
- 🌍 תמיכה מלאה בעברית
- 📱 ממשק אינטואיטיבי עם כפתורים

## 🏗️ ארכיטקטורה

```
Frontend:  Telegram Bot (python-telegram-bot)
Backend:   Quart + Hypercorn (async)
Database:  MongoDB Atlas (Free Tier)
Hosting:   Render (Free Tier)
```

## 📁 מבנה הפרויקט

```
url-shortener-bot/
├── bot.py              # לוגיקת הבוט (handlers, commands)
├── app.py              # Quart server (webhook, redirect)
├── database.py         # MongoDB operations
├── utils.py            # Helper functions (Base62, QR, etc)
├── config.py           # Configuration & messages
├── keyboards.py        # Inline keyboards
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── render.yaml         # Render deployment config
└── README.md           # זה!
```

## 🚀 התקנה מהירה

### 1. צור בוט בטלגרם

1. פתח את [@BotFather](https://t.me/BotFather)
2. שלח `/newbot`
3. בחר שם ו-username לבוט
4. שמור את ה-**Bot Token**

### 2. הגדר MongoDB

1. צור חשבון ב-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (חינם)
2. צור Cluster חדש (M0 - Free)
3. לחץ על "Connect" -> "Connect your application"
4. העתק את ה-**Connection String**
5. החלף את `<password>` בסיסמה שלך

### 3. Deploy ל-Render

#### אופציה א': דרך Dashboard

1. צור חשבון ב-[Render](https://render.com)
2. לחץ על "New +" -> "Web Service"
3. חבר את GitHub repository שלך
4. Render יזהה את `render.yaml` אוטומטית
5. הגדר את המשתנים (ראה למטה)
6. לחץ על "Create Web Service"

#### אופציה ב': דרך Blueprint

1. Fork את ה-repository הזה
2. לחץ על: [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
3. הגדר את המשתנים
4. Deploy!

### 4. הגדרת משתני סביבה ב-Render

בעמוד ה-Dashboard של השירות שלך, לך ל-"Environment" והגדר:

| Variable | Value | Example |
|----------|-------|---------|
| `BOT_TOKEN` | הטוקן מ-BotFather | `1234567890:ABCdef...` |
| `WEBHOOK_URL` | ה-URL של האפליקציה ב-Render | `https://your-app.onrender.com` |
| `BASE_URL` | אותו URL | `https://your-app.onrender.com` |
| `MONGODB_URI` | Connection string מ-MongoDB | `mongodb+srv://...` |

**שאר המשתנים** נמצאים ב-`render.yaml` עם ערכי ברירת מחדל.

### 5. אתחול ראשוני

אחרי שה-Deploy מסתיים:

1. העתק את ה-URL של האפליקציה (למשל: `https://your-app.onrender.com`)
2. פתח בדפדפן: `https://your-app.onrender.com/health`
3. אמור להופיע: `{"status":"healthy"}`
4. פתח את הבוט בטלגרם ושלח `/start`

🎉 **הבוט פועל!**

## 📖 שימוש

### פקודות זמינות

- `/start` - תפריט ראשי
- `/shorten` - קיצור קישור חדש
- `/mylinks` - הצגת כל הקישורים שלך
- `/stats` - סטטיסטיקות כלליות
- `/help` - עזרה

### תרחישי שימוש

#### קיצור קישור

1. שלח `/shorten` או לחץ "🔗 קצר קישור חדש"
2. שלח את הקישור הארוך
3. קבל קישור קצר מיידית!

#### צפייה בסטטיסטיקות

1. שלח `/mylinks`
2. בחר קישור מהרשימה
3. לחץ "📊 סטטיסטיקות"

#### יצירת QR Code

1. בחר קישור כלשהו
2. לחץ "🖼️ צור QR Code"
3. קבל תמונת QR מיד!

## 🔧 הרצה מקומית (Development)

### דרישות

- Python 3.11+
- MongoDB (מקומי או Atlas)
- חשבון בוט בטלגרם

### התקנה

```bash
# שכפל את הפרויקט
git clone https://github.com/yourusername/url-shortener-bot.git
cd url-shortener-bot

# צור virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# התקן dependencies
pip install -r requirements.txt

# העתק .env.example ל-.env
cp .env.example .env

# ערוך את .env עם הפרטים שלך
nano .env  # or vim, code, etc.
```

### הרצה

#### Polling Mode (לפיתוח)

```bash
python bot.py
```

הבוט יתחיל לשלוף עדכונים ישירות מטלגרם.

#### Webhook Mode (כמו בפרודקשן)

```bash
# Terminal 1 - הרץ את השרת (Quart)
python app.py

# Terminal 2 - הגדר webhook (פעם אחת)
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-ngrok-url.ngrok.io/<YOUR_BOT_TOKEN>"
```

**טיפ:** השתמש ב-[ngrok](https://ngrok.com) כדי לחשוף localhost:

```bash
ngrok http 5000
```

## 🌐 API Endpoints

הבוט מספק גם API פשוט:

### `POST /api/shorten`

קיצור URL ללא בוט.

**Request:**
```json
{
  "url": "https://example.com/very/long/url",
  "user_id": 123456  // optional
}
```

**Response:**
```json
{
  "short_url": "https://your-app.onrender.com/dQw4w9",
  "short_code": "dQw4w9",
  "original_url": "https://example.com/very/long/url"
}
```

### `GET /<short_code>`

Redirect לכתובת המקורית.

**Example:**
```
https://your-app.onrender.com/dQw4w9
-> Redirects to original URL
```

### `GET /qr/<short_code>`

קבלת QR code כתמונה.

**Example:**
```
https://your-app.onrender.com/qr/dQw4w9
-> Returns PNG image
```

### `GET /api/stats/<short_code>`

קבלת סטטיסטיקות של קישור.

**Response:**
```json
{
  "short_code": "dQw4w9",
  "original_url": "https://example.com/...",
  "short_url": "https://your-app.onrender.com/dQw4w9",
  "clicks": 42,
  "created_at": "24/12/2024 15:30",
  "last_clicked": "25/12/2024 10:15"
}
```

## ⚙️ קונפיגורציה מתקדמת

### Rate Limiting

שנה את הגבלות השימוש ב-`.env`:

```env
MAX_URLS_PER_HOUR=10     # מקסימום קישורים לשעה
MAX_URLS_PER_DAY=50      # מקסימום קישורים ליום
```

### חסימת דומיינים

הוסף דומיינים לרשימה השחורה:

```env
BLOCKED_DOMAINS=malicious.com,spam.site,phishing.net
```

### קוד קצר

שנה את אורך הקוד הקצר (3-10):

```env
SHORT_CODE_LENGTH=6  # dQw4w9 (ברירת מחדל)
```

## 🛡️ אבטחה

### מה הבוט כולל:

- ✅ ולידציה של URLs
- ✅ חסימת דומיינים זדוניים
- ✅ Rate Limiting
- ✅ אימות בעלות על קישורים (למחיקה)
- ✅ Sanitization של inputs

### מה כדאי להוסיף (Phase 2):

- 🔐 הצפנת URLs רגישים
- 🔒 הגנת סיסמה לקישורים
- 📊 Audit logs
- 🚫 CAPTCHA למניעת בוטים

## 📊 מסד הנתונים

### Schema

#### Collection: `urls`

```javascript
{
  _id: ObjectId,
  user_id: Number,        // Telegram user ID
  original_url: String,
  short_code: String,     // Unique index
  created_at: Date,
  clicks: Number,
  last_clicked: Date
}
```

#### Collection: `users`

```javascript
{
  _id: ObjectId,
  user_id: Number,        // Unique index
  username: String,
  first_name: String,
  last_name: String,
  created_at: Date,
  last_seen: Date
}
```

### Indexes

```javascript
// urls collection
db.urls.createIndex({ short_code: 1 }, { unique: true })
db.urls.createIndex({ user_id: 1 })
db.urls.createIndex({ user_id: 1, created_at: -1 })

// users collection
db.users.createIndex({ user_id: 1 }, { unique: true })
```

## 🐛 Debugging

### בדיקת לוגים ב-Render

1. לך ל-Dashboard -> שירות שלך -> "Logs"
2. תראה את כל הלוגים בזמן אמת

### שגיאות נפוצות

#### "Bot token is invalid"
- בדוק שה-`BOT_TOKEN` נכון ב-Environment Variables

#### "Failed to connect to MongoDB"
- בדוק את ה-`MONGODB_URI`
- וודא ש-IP של Render מורשה ב-MongoDB Atlas (הוסף `0.0.0.0/0`)

#### "Webhook failed"
- בדוק שה-`WEBHOOK_URL` תואם ל-URL של האפליקציה
- נסה להגדיר את ה-webhook מחדש:
  ```bash
  curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
    -d "url=https://your-app.onrender.com/<TOKEN>"
  ```

## 🔄 עדכונים

### איך לעדכן את הבוט

1. Push שינויים ל-GitHub
2. Render יעשה Deploy אוטומטי (אם הגדרת `autoDeploy: true`)
3. הבוט יעבוד עם הקוד החדש אחרי ~2-3 דקות

## 💡 פיצ'רים עתידיים (Phase 2)

- [ ] Custom short codes (למשל: `/mycompany`)
- [ ] תפוגת קישורים (expire after X days)
- [ ] Password protection לקישורים
- [ ] Analytics מתקדם עם גרפים
- [ ] Export נתונים ל-CSV
- [ ] תמיכה בדומיינים מותאמים אישית
- [ ] A/B Testing (מספר קישורים לאותו URL)
- [ ] Geo-targeting (redirect לפי מיקום)

## 🤝 תרומה

רוצה לתרום? מעולה!

1. Fork את הפרויקט
2. צור branch חדש (`git checkout -b feature/amazing-feature`)
3. Commit את השינויים (`git commit -m 'Add amazing feature'`)
4. Push ל-branch (`git push origin feature/amazing-feature`)
5. פתח Pull Request

## 📄 רישיון

MIT License - ראה את קובץ `LICENSE` לפרטים.

## 👨‍💻 יוצר

**אמיר חיים**

- Telegram: [@your_username](https://t.me/your_username)
- GitHub: [@your_github](https://github.com/your_github)

## 🙏 תודות

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Quart](https://pgjones.gitlab.io/quart/)
- [MongoDB](https://www.mongodb.com/)
- [Render](https://render.com/)

---

**נהנית מהבוט? תן ⭐ ל-repository!**
