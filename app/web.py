from aiohttp import web
from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import hmac, hashlib
from app.config import get_settings
from app.bot import create_bot
from app.handlers import start, admin, echo

settings = get_settings()
bot = create_bot(settings.bot_token)
dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(admin.router)
dp.include_router(echo.router)

async def on_startup(app: web.Application):
    # تعيين الويبهوك إلى مسار التطبيق العام
    # Render يوفر URL عام تلقائياً، سنستخدم المسار /webhook
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{app['base_url']}/webhook", secret_token=settings.webhook_secret)
    print("Webhook set")

async def on_shutdown(app: web.Application):
    await bot.session.close()
    print("Shutdown complete")

async def verify_signature(request: web.Request):
    body = await request.read()
    signature = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    # تحقق بسيط — تلغرام يرسل نفس القيمة التي وضعناها كـ secret_token
    if not hmac.compare_digest(signature, settings.webhook_secret):
        raise web.HTTPUnauthorized()
    request._body = body  # خزّن المحتوى ليستخدمه المعالج لاحقاً

async def health(_request: web.Request):
    return web.json_response({"status": "ok"})

def create_app(base_url: str) -> web.Application:
    app = web.Application()
    app['base_url'] = base_url
    app.add_routes([web.get("/health", health)])

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    setup_application(app, dp, bot=bot)
    return app

# نقطة الدخول
def init_app():
    # على Render، يمكننا الحصول على BASE_URL من المتغير البيئي أو ضبطه لاحقاً في README
    base_url = os.getenv("APP_BASE_URL", "").strip()
    if not base_url:
        # إن لم يتوفر، سنعتمد أن المستخدم سيضبطه يدوياً بعد أول نشر (انظر README)
        print("Warning: APP_BASE_URL not set. Set it to your Render public URL.")
        base_url = "https://example.onrender.com"
    return create_app(base_url)
