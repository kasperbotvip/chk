import os
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from pytube import YouTube

# token
BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg")

# حماية
MAX_DURATION_MIN = 15          # أقصى مدة مسموح تحميلها
MAX_FILE_SIZE_MB = 45          # أقصى حجم مسموح لإرساله
RATE_LIMIT_SECONDS = 20        # سبام حماية: كل مستخدم ينتظر 20 ثانية

user_last_request = {}         # حفظ وقت آخر طلب لكل مستخدم


# =============== أدوات مساعدة ===============

def bytes_to_mb(b):
    return b / (1024 * 1024)

def check_rate_limit(user_id):
    """يحارب السبام لكل مستخدم"""
    now = time.time()
    last = user_last_request.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return int(RATE_LIMIT_SECONDS - (now - last))
    user_last_request[user_id] = now
    return 0


# =============== أوامر البوت ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا بك! 🙌\n"
        "هذا بوت تحميل مقاطع اليوتيوب 🎥🎧\n"
        "أرسل رابط YouTube واختار نوع التحميل والجودة.\n"
        "البوت مفتوح للجميع ✔"
    )


# =============== استقبال الرابط ===============

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    url = update.message.text.strip()
    user_id = update.message.from_user.id

    # حماية سبام
    wait = check_rate_limit(user_id)
    if wait > 0:
        await update.message.reply_text(f"⏳ انتظر {wait} ثانية قبل تحميل جديد.")
        return

    # تحقق أنه رابط يوتيوب
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ الرجاء إرسال رابط يوتيوب فقط.")
        return

    context.user_data["url"] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 تحميل فيديو", callback_data="type:video"),
            InlineKeyboardButton("🎧 تحميل صوت", callback_data="type:audio"),
        ]
    ]

    await update.message.reply_text(
        "اختر نوع التحميل:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =============== ضغط الأزرار ===============

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    url = user_data.get("url")

    if not url:
        await query.edit_message_text("⚠ أرسل رابط يوتيوب أولًا.")
        return

    data = query.data

    # 1) نوع التحميل
    if data.startswith("type:"):
        dl_type = data.split(":")[1]  # video أو audio
        user_data["type"] = dl_type

        if dl_type == "video":
            kb = [
                [
                    InlineKeyboardButton("360p", callback_data="v:360p"),
                    InlineKeyboardButton("480p", callback_data="v:480p"),
                ],
                [
                    InlineKeyboardButton("720p", callback_data="v:720p"),
                    InlineKeyboardButton("أعلى جودة", callback_data="v:best"),
                ],
            ]
            await query.edit_message_text(
                "اختر جودة الفيديو:", reply_markup=InlineKeyboardMarkup(kb)
            )

        else:
            kb = [[InlineKeyboardButton("🎧 أفضل جودة صوت", callback_data="a:best")]]
            await query.edit_message_text(
                "اختر جودة الصوت:", reply_markup=InlineKeyboardMarkup(kb)
            )
        return

    # 2) جودة الفيديو
    if data.startswith("v:"):
        quality = data.split(":")[1]
        await download_video(query, context, url, quality)
        return

    # 3) جودة الصوت
    if data.startswith("a:"):
        await download_audio(query, context, url)
        return


# =============== تحميل الفيديو ===============

async def download_video(query, context, url, quality):
    await query.edit_message_text("⏳ جاري تجهيز الفيديو…")

    try:
        yt = YouTube(url)
        duration = yt.length / 60

        if duration > MAX_DURATION_MIN:
            await query.edit_message_text(f"⚠ الفيديو طويل ({int(duration)} دقيقة). الحد: {MAX_DURATION_MIN}")
            return

        # اختيار الجودة
        if quality == "best":
            stream = yt.streams.filter(progressive=True, file_extension="mp4").get_highest_resolution()
        else:
            stream = yt.streams.filter(progressive=True, file_extension="mp4", res=quality).first()
            if not stream:
                stream = yt.streams.filter(progressive=True, file_extension="mp4").get_highest_resolution()

        await query.edit_message_text("⬇️ جاري التحميل…")

        file_path = stream.download()
        size_mb = bytes_to_mb(os.path.getsize(file_path))

        if size_mb > MAX_FILE_SIZE_MB:
            os.remove(file_path)
            await query.edit_message_text(f"⚠ حجم الفيديو {size_mb:.1f}MB يتجاوز الحد {MAX_FILE_SIZE_MB}MB")
            return

        await query.edit_message_text("📤 جاري إرسال الفيديو…")

        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=open(file_path, "rb"),
            caption=f"{yt.title}\nالجودة: {stream.resolution}",
        )

        os.remove(file_path)

    except Exception as e:
        await query.edit_message_text(f"❌ خطأ في التحميل:\n{e}")


# =============== تحميل الصوت ===============

async def download_audio(query, context, url):
    await query.edit_message_text("⏳ جاري تجهيز الصوت…")

    try:
        yt = YouTube(url)
        duration = yt.length / 60

        if duration > MAX_DURATION_MIN:
            await query.edit_message_text(f"⚠ الصوت طويل ({int(duration)} دقيقة). الحد: {MAX_DURATION_MIN}")
            return

        stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        file_path = stream.download()

        size_mb = bytes_to_mb(os.path.getsize(file_path))
        if size_mb > MAX_FILE_SIZE_MB:
            os.remove(file_path)
            await query.edit_message_text(f"⚠ حجم الصوت {size_mb:.1f}MB يتجاوز الحد.")
            return

        await query.edit_message_text("📤 جاري إرسال الصوت…")

        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=open(file_path, "rb"),
            title=yt.title,
            caption="🎧 تم استخراج الصوت",
        )

        os.remove(file_path)

    except Exception as e:
        await query.edit_message_text(f"❌ خطأ:\n{e}")


# =============== تشغيل البوت ===============

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN غير موجود")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # هاندلرات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(buttons))

    print("🚀 البوت يعمل الآن…")
    app.run_polling()   # لاحظ: لا يوجد await ولا asyncio.run()

if __name__ == "__main__":
    main()
