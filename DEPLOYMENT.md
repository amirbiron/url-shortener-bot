# 🚀 מדריך Deploy מפורט

## 📋 דרישות מקדימות

לפני שמתחילים, ודא שיש לך:

- [x] חשבון GitHub
- [x] חשבון Render (חינם)
- [x] חשבון MongoDB Atlas (חינם)
- [x] בוט טלגרם (דרך @BotFather)

---

## שלב 1: הגדרת הבוט בטלגרם

### 1.1 יצירת הבוט

1. פתח את [@BotFather](https://t.me/BotFather) בטלגרם
2. שלח: `/newbot`
3. בחר שם לבוט (למשל: "My URL Shortener")
4. בחר username (חייב להסתיים ב-`bot`, למשל: `myurl_shortener_bot`)
5. **שמור את ה-Token!** זה ייראה כך:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
   ```

### 1.2 הגדרת פקודות (אופציונלי אבל מומלץ)

1. שלח ל-@BotFather: `/setcommands`
2. בחר את הבוט שלך
3. שלח את הרשימה הבאה:

```
start - תפריט ראשי
shorten - קיצור קישור חדש
mylinks - הקישורים שלי
stats - סטטיסטיקות
help - עזרה
```

---

## שלב 2: הגדרת MongoDB Atlas

### 2.1 יצירת Cluster

1. לך ל-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. צור חשבון (או התחבר)
3. לחץ "Build a Database"
4. בחר **M0 (FREE)**
5. בחר Region קרוב אליך (למשל: Frankfurt)
6. לחץ "Create"

### 2.2 הגדרת אבטחה

#### Database Access:

1. לך ל-"Database Access" (בצד שמאל)
2. לחץ "Add New Database User"
3. בחר שם משתמש וסיסמה (**שמור אותם!**)
4. Role: "Atlas Admin"
5. לחץ "Add User"

#### Network Access:

1. לך ל-"Network Access"
2. לחץ "Add IP Address"
3. לחץ "Allow Access from Anywhere" (או הוסף `0.0.0.0/0`)
4. לחץ "Confirm"

### 2.3 קבלת Connection String

1. לך ל-"Database" -> "Connect"
2. בחר "Connect your application"
3. Driver: **Python**, Version: **3.11 or later**
4. העתק את ה-Connection String:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **החלף** את `<username>` ו-`<password>` בערכים האמיתיים שלך!

---

## שלב 3: הכנת הקוד

### 3.1 Clone/Fork Repository

אם הקוד ב-GitHub שלך:
```bash
git clone https://github.com/YOUR_USERNAME/url-shortener-bot.git
cd url-shortener-bot
```

אם עדיין לא העלית:
```bash
# התחל repository חדש
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/url-shortener-bot.git
git push -u origin main
```

### 3.2 בדיקת הקבצים

ודא שכל הקבצים קיימים:

```bash
ls -la
```

אתה אמור לראות:
```
bot.py
app.py
database.py
utils.py
config.py
keyboards.py
requirements.txt
render.yaml
.env.example
.gitignore
README.md
```

---

## שלב 4: Deploy ל-Render

### 4.1 יצירת Web Service

1. לך ל-[Render Dashboard](https://dashboard.render.com/)
2. לחץ **"New +"** -> **"Web Service"**
3. חבר את GitHub repository שלך:
   - אם זו הפעם הראשונה: לחץ "Connect account" ואשר ל-Render גישה
   - בחר את ה-repository: `url-shortener-bot`
4. Render יזהה את `render.yaml` אוטומטית

### 4.2 הגדרת השירות

אם Render **לא** קרא את `render.yaml`, מלא ידנית:

| Field | Value |
|-------|-------|
| Name | `url-shortener-bot` |
| Region | Frankfurt (או קרוב אליך) |
| Branch | `main` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `hypercorn app:app --bind 0.0.0.0:$PORT` |

### 4.3 הגדרת Environment Variables

גלול למטה ל-**"Environment Variables"** ולחץ "Add Environment Variable".

הוסף **אחד אחד**:

| Key | Value | הערות |
|-----|-------|-------|
| `BOT_TOKEN` | `1234567890:ABC...` | מ-@BotFather |
| `MONGODB_URI` | `mongodb+srv://...` | מ-MongoDB Atlas |
| `WEBHOOK_SECRET_TOKEN` | `...` | טוקן סודי ל-webhook (לא ה-BOT_TOKEN). חייב להיות רק [A-Za-z0-9_-] |
| `WEBHOOK_URL` | *(נשאיר ריק כרגע)* | נעדכן אחר כך |
| `BASE_URL` | *(נשאיר ריק כרגע)* | נעדכן אחר כך |
| `DB_NAME` | `url_shortener` | |
| `SECRET_KEY` | (לחץ Generate) | Render יצור אוטומטית |
| `DEBUG` | `False` | |

**שאר המשתנים** נמצאים ב-`render.yaml` עם ערכי ברירת מחדל.

### 4.4 Deploy!

1. לחץ **"Create Web Service"**
2. Render יתחיל לבנות את האפליקציה (~2-3 דקות)
3. המתן עד שתראה: ✅ **"Live"**

### 4.5 עדכון WEBHOOK_URL ו-BASE_URL

1. העתק את ה-URL של האפליקציה:
   ```
   https://url-shortener-bot-xxxx.onrender.com
   ```
2. לך ל-**"Environment"** בצד שמאל
3. ערוך את `WEBHOOK_URL` ו-`BASE_URL` לאותו URL
4. לחץ **"Save Changes"**
5. Render יעשה Deploy מחדש אוטומטית

---

## שלב 5: אימות שהכל עובד

### 5.1 בדיקת Health

פתח בדפדפן:
```
https://your-app-name.onrender.com/health
```

אתה אמור לראות:
```json
{
  "status": "healthy",
  "service": "url-shortener-bot"
}
```

### 5.2 בדיקת הבוט

1. פתח את הבוט בטלגרם
2. שלח `/start`
3. אתה אמור לראות את התפריט הראשי! 🎉

---

## 🐛 פתרון בעיות

### הבוט לא עונה

#### 1. בדוק את הלוגים

1. לך ל-Render Dashboard -> השירות שלך -> **"Logs"**
2. חפש שגיאות (בדרך כלל באדום)

#### 2. בדוק Webhook

הרץ את הפקודה הזו (החלף `<TOKEN>` ב-Bot Token שלך):

```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

אתה אמור לראות:
```json
{
  "url": "https://your-app.onrender.com/telegram/webhook",
  "has_custom_certificate": false,
  "pending_update_count": 0,
  "last_error_date": 0
}
```

אם `url` ריק או שגוי, הגדר את ה-Webhook מחדש:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-app.onrender.com/<TOKEN>"
```

#### 3. בדוק MongoDB Connection

אם יש שגיאת "Failed to connect to MongoDB":

1. ודא שה-`MONGODB_URI` נכון (עם username/password)
2. ודא שהוספת `0.0.0.0/0` ב-Network Access של MongoDB
3. נסה את ה-connection string בדפדפן:
   ```
   https://cloud.mongodb.com/
   ```

### שגיאת "Module not found"

אם יש שגיאה כמו `ModuleNotFoundError: No module named 'telegram'`:

1. ודא ש-`requirements.txt` קיים
2. ודא שה-Build Command הוא: `pip install -r requirements.txt`
3. עשה Deploy מחדש

### האפליקציה "sleeps" (Free Tier)

Render Free Tier עובר ל-sleep אחרי 15 דקות ללא פעילות.

**פתרון:**
1. השתמש ב-[UptimeRobot](https://uptimerobot.com/) (חינם)
2. הוסף monitor ל-URL:
   ```
   https://your-app.onrender.com/health
   ```
3. UptimeRobot יבדוק כל 5 דקות ויעיר את האפליקציה

---

## 🔄 עדכונים עתידיים

### איך לעדכן את הבוט

1. ערוך את הקוד locally
2. Commit ו-Push:
   ```bash
   git add .
   git commit -m "Update: new feature"
   git push origin main
   ```
3. Render יעשה Deploy אוטומטית! ⚡

---

## 📊 מעקב ושיפורים

### Logs

צפה בלוגים בזמן אמת:
```
Render Dashboard -> שירות שלך -> Logs
```

### Metrics

ב-Render Dashboard תוכל לראות:
- CPU Usage
- Memory Usage
- Request Count

### Database

בדוק את המסד נתונים:
```
MongoDB Atlas -> Database -> Browse Collections
```

---

## ✅ Checklist סופי

לפני שמסיימים, ודא:

- [x] הבוט עונה ל-`/start`
- [x] ניתן לקצר קישורים
- [x] Redirect עובד (https://your-app.onrender.com/xxxxxx)
- [x] QR Codes נוצרים
- [x] סטטיסטיקות מוצגות
- [x] MongoDB מקבל נתונים (בדוק ב-Atlas)
- [x] הגדרת UptimeRobot (כדי שלא יירדם)

---

## 🎉 סיימת!

הבוט שלך פועל ב-production!

**מה הלאה?**
- הוסף פיצ'רים (ראה `README.md` -> Phase 2)
- שתף עם חברים
- תן ⭐ ל-repository אם נהנית!

**צריך עזרה?**
- פתח Issue ב-GitHub
- שלח הודעה ב-Telegram

---

**נהנית? שתף! ⭐**
