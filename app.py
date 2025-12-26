"""
URL Shortener Bot - Quart Server
=================================
שרת Quart (ASGI) עם webhook לטלגרם ו-routes לקיצור URLs
"""

from quart import Quart, request, redirect, jsonify, send_file
import logging
from telegram import Update
from config import Config
from database import get_url, increment_clicks
from bot import create_bot_application
import asyncio
from contextlib import suppress

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# יצירת Quart app (ASGI) - מתאים ל-Hypercorn ול-async lifecycle hooks
app = Quart(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# יצירת bot application
bot_application = create_bot_application()

# Background lifecycle state (avoid blocking Hypercorn lifespan startup)
_services_task: asyncio.Task | None = None
_bot_ready: asyncio.Event = asyncio.Event()


# ==================== Routes ====================

@app.route('/')
async def index():
    """
    עמוד הבית
    """
    return jsonify({
        'status': 'ok',
        'service': 'URL Shortener Bot',
        'version': '1.0.0'
    })


@app.route('/health')
async def health():
    """
    בדיקת תקינות השרת
    """
    return jsonify({
        'status': 'healthy',
        'service': 'url-shortener-bot'
    }), 200


WEBHOOK_PATH = "/telegram/webhook"


@app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook():
    """
    Webhook לקבלת עדכונים מטלגרם
    """
    try:
        # If the service is still starting (e.g., Telegram init / webhook setup),
        # don't block the request handler or fail with 500s.
        if not _bot_ready.is_set():
            return jsonify({"status": "starting"}), 503

        # אימות בסיסי: Telegram ישלח את ה-secret token ב-header
        # כך לא צריך לחשוף את BOT_TOKEN ב-URL (וגם נמנעות בעיות עם ':' בנתיב).
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not secret or secret != Config.WEBHOOK_SECRET_TOKEN:
            return jsonify({"status": "forbidden"}), 403

        # קבלת העדכון מטלגרם
        json_data = await request.get_json()
        
        if not json_data:
            return jsonify({'status': 'error', 'message': 'No data'}), 400
        
        # המרה ל-Update object
        update = Update.de_json(json_data, bot_application.bot)
        
        # עיבוד העדכון
        await bot_application.process_update(update)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/<short_code>')
async def redirect_url(short_code):
    """
    Redirect מקוד קצר ל-URL המקורי
    
    Args:
        short_code: הקוד הקצר
        
    Returns:
        Redirect או 404
    """
    try:
        # משיכת ה-URL מה-DB
        url_doc = get_url(short_code)
        
        if not url_doc:
            return jsonify({
                'error': 'URL not found',
                'short_code': short_code
            }), 404
        
        # עדכון מונה הקליקים
        increment_clicks(short_code)
        
        # Redirect
        original_url = url_doc['original_url']
        
        logger.info(f"Redirecting {short_code} -> {original_url}")
        
        return redirect(original_url, code=301)
        
    except Exception as e:
        logger.error(f"Error in redirect: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/qr/<short_code>')
async def qr_code(short_code):
    """
    יצירת QR code עבור קישור
    
    Args:
        short_code: הקוד הקצר
        
    Returns:
        תמונת QR או 404
    """
    try:
        # בדיקה שהקוד קיים
        url_doc = get_url(short_code)
        
        if not url_doc:
            return jsonify({
                'error': 'URL not found',
                'short_code': short_code
            }), 404
        
        # יצירת QR
        from utils import generate_qr
        short_url = f"{Config.BASE_URL}/{short_code}"
        qr_image = generate_qr(short_url)
        
        # שליחת התמונה
        return await send_file(
            qr_image,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'qr_{short_code}.png'
        )
        
    except Exception as e:
        logger.error(f"Error generating QR: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/stats/<short_code>')
async def get_stats(short_code):
    """
    משיכת סטטיסטיקות של קישור (API endpoint)
    
    Args:
        short_code: הקוד הקצר
        
    Returns:
        JSON עם סטטיסטיקות
    """
    try:
        url_doc = get_url(short_code)
        
        if not url_doc:
            return jsonify({
                'error': 'URL not found',
                'short_code': short_code
            }), 404
        
        # החזרת נתונים
        from utils import DateFormatter
        
        stats = {
            'short_code': short_code,
            'original_url': url_doc['original_url'],
            'short_url': f"{Config.BASE_URL}/{short_code}",
            'clicks': url_doc.get('clicks', 0),
            'created_at': DateFormatter.format_datetime(url_doc['created_at']),
            'last_clicked': None
        }
        
        if url_doc.get('last_clicked'):
            stats['last_clicked'] = DateFormatter.format_datetime(url_doc['last_clicked'])
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/shorten', methods=['POST'])
async def api_shorten():
    """
    API endpoint לקיצור URL (לשימוש חיצוני עתידי)
    
    Body:
        {
            "url": "https://example.com/long/url",
            "user_id": 123456 (optional)
        }
    
    Returns:
        JSON עם הקישור הקצר
    """
    try:
        data = await request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing URL parameter'
            }), 400
        
        url = data['url']
        user_id = data.get('user_id', 0)  # 0 = anonymous
        
        # ולידציה
        from utils import validate_url, generate_short_code, URLValidator
        
        url = URLValidator.normalize_url(url)
        is_safe, reason = validate_url(url)
        
        if not is_safe:
            return jsonify({
                'error': f'Invalid URL: {reason}'
            }), 400
        
        # בדיקה אם כבר קיים
        from database import url_repo, create_url
        
        existing = url_repo.find_existing(user_id, url)
        
        if existing:
            short_code = existing['short_code']
        else:
            # יצירת קוד חדש
            short_code = None
            for _ in range(5):
                temp_code = generate_short_code()
                if not get_url(temp_code):
                    short_code = temp_code
                    break
            
            if not short_code:
                return jsonify({
                    'error': 'Failed to generate short code'
                }), 500
            
            # שמירה
            url_doc = create_url(user_id, url, short_code)
            
            if not url_doc:
                return jsonify({
                    'error': 'Failed to create URL'
                }), 500
        
        # החזרת תוצאה
        short_url = f"{Config.BASE_URL}/{short_code}"
        
        return jsonify({
            'short_url': short_url,
            'short_code': short_code,
            'original_url': url
        }), 200
        
    except Exception as e:
        logger.error(f"Error in API shorten: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== Error Handlers ====================

@app.errorhandler(404)
async def not_found(error):
    """טיפול ב-404"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
async def internal_error(error):
    """טיפול ב-500"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on our end'
    }), 500


# ==================== Webhook Setup ====================

async def setup_webhook():
    """
    הגדרת webhook לטלגרם
    """
    try:
        webhook_url = f"{Config.WEBHOOK_URL}{WEBHOOK_PATH}"
        
        await bot_application.bot.set_webhook(
            url=webhook_url,
            secret_token=Config.WEBHOOK_SECRET_TOKEN,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        logger.info(f"✅ Webhook set to: {webhook_url}")
        
    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        raise


async def remove_webhook():
    """
    הסרת webhook (לפיתוח מקומי)
    """
    try:
        await bot_application.bot.delete_webhook()
        logger.info("✅ Webhook removed")
    except Exception as e:
        logger.error(f"❌ Error removing webhook: {e}")


# ==================== Application Lifecycle ====================

async def _start_services_in_background():
    """
    Start Telegram bot + configure webhook without blocking ASGI lifespan startup.
    Any failure here should not prevent the web server from coming up (Render health checks).
    """
    global bot_application
    backoff_seconds = 2
    max_attempts = 10
    bot_started = False

    for attempt in range(1, max_attempts + 1):
        try:
            # Start bot (if not already running)
            if not bot_started:
                logger.info("🤖 Initializing Telegram bot...")
                await bot_application.initialize()
                await bot_application.start()
                bot_started = True
                logger.info("✅ Telegram bot started")

            # Configure webhook (production only)
            if not Config.DEBUG:
                logger.info("🔗 Setting Telegram webhook...")
                await setup_webhook()
            else:
                logger.info("⚠️ Running in DEBUG mode - webhook disabled")

            _bot_ready.set()
            logger.info("✅ Background services ready")
            return
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Don't raise: keep the web server alive; retry a few times for transient failures.
            logger.exception(f"❌ Background startup failed (attempt {attempt}/{max_attempts}): {e}")
            bot_started = False

            # Best-effort cleanup to avoid leaving the PTB Application in a half-started state.
            with suppress(Exception):
                await bot_application.stop()
            with suppress(Exception):
                await bot_application.shutdown()

            # Re-create the bot application for the next attempt (fresh internal state).
            with suppress(Exception):
                bot_application = create_bot_application()

            if attempt < max_attempts:
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 60)

    logger.error("❌ Background startup gave up after repeated failures")


@app.before_serving
async def startup():
    """
    אתחול השרת
    """
    logger.info("🚀 Starting Quart server...")

    # IMPORTANT:
    # Hypercorn enforces an ASGI lifespan startup timeout. Any slow network calls
    # (Telegram API, DNS, etc.) here can cause "Lifespan failure in startup. 'Timed out'".
    # So we start the bot/webhook in the background and return immediately.
    global _services_task
    if _services_task is None or _services_task.done():
        _services_task = asyncio.create_task(_start_services_in_background())

    logger.info("✅ Server started (background init running)")


@app.after_serving
async def shutdown():
    """
    סגירת השרת
    """
    logger.info("⏹️ Shutting down server...")

    # Stop background startup task if still running
    global _services_task
    if _services_task and not _services_task.done():
        _services_task.cancel()
        with suppress(Exception):
            await _services_task
    
    # סגירת הבוט
    # בפרודקשן לא מוחקים webhook בזמן shutdown, כי restarts/deploys יגרמו
    # לבוט "להיעלם" עד שה-service עולה שוב ומגדיר webhook מחדש.
    # מחיקה מיועדת רק לפיתוח מקומי (polling).
    if Config.DEBUG:
        await remove_webhook()

    with suppress(Exception):
        await bot_application.stop()
    with suppress(Exception):
        await bot_application.shutdown()
    
    # סגירת MongoDB
    from database import db
    db.close()
    
    logger.info("✅ Server shut down successfully")


# ==================== Run Server ====================

if __name__ == '__main__':
    # הרצה מקומית (development)
    import asyncio
    
    async def run_dev():
        """הרצת שרת פיתוח"""
        # הסרת webhook אם קיים
        await bot_application.initialize()
        await remove_webhook()
        await bot_application.shutdown()
        
        # הרצת Quart (development)
        await app.run_task(
            host='0.0.0.0',
            port=Config.PORT,
            debug=Config.DEBUG
        )
    
    asyncio.run(run_dev())
