import os
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
# مهم: استخدم pytubefix بدل pytube
from pytubefix import YouTube

# التوكن من متغير البيئة (على Render حط BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAG-F0MqkTVJkhmG5TaX6sxcD0NeXOohnis")

# إعدادات حماية
MAX_DURATION_MIN = 15          # أقصى مدة للفيديو بالدقائق
MAX_FILE_SIZE_MB = 45          # أقصى حجم تقريبي للملف المرسل
RATE_LIMIT_SECONDS = 20        # كل مستخدم ينتظر 20 ثانية بين التحميلات

user_last_request = {}         # لتتبع آخر طلب لكل مستخدم


# ========= دوال مساعدة =========

def bytes_to_mb(size_bytes: int) -> float:
    return size_bytes / (1024 * 1024)


def check_rate_limit(user_id: int) -> int:
    """
    يرجّع كم ثانية باقي ينتظر المستخدم لو مسوي سبام.
    لو 0 يعني مسموح يحمل.
    """
    now = time.time()
    last = user_last_request.get(user_id, 0)
    diff = now - last
    if diff < RATE_LIMIT_SECONDS:
        return int(RATE_LIMIT_SECONDS - diff)
    user_last_request[user_id] = now
    return 0


# ========= /start =========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا 🙌\n"
        "أنا بوت تحميل من يوتيوب 🎥🎧\n\n"
        "▫️ أرسل رابط فيديو من YouTube\n"
        "▫️ بعدها راح تطلع لك أزرار: تحميل فيديو أو صوت\n"
        "▫️ تختار الجودة وبس 👍"
    )


# ========= استقبال رابط اليوتيوب =========

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    user_id = update.message.from_user.id

    # سبام
    wait_sec = check_rate_limit(user_id)
    if wait_sec > 0:
        await update.message.reply_text(
            f"⏳ رجاءً انتظر {wait_sec} ثانية قبل طلب تحميل جديد."
        )
        return

    # تأكد إنه يوتيوب
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ أرسل رابط من YouTube فقط.")
        return

    # خزِّن الرابط في user_data (خاص بالمستخدم)
    context.user_data["yt_url"] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 تحميل فيديو", callback_data="type:video"),
            InlineKeyboardButton("🎧 تحميل صوت", callback_data="type:audio"),
        ]
    ]
    await update.message.reply_text(
        "اختر نوع التحميل:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ========= التعامل مع الأزرار =========

async def buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_data = context.user_data
    url = user_data.get("yt_url")

    if not url:
        await query.edit_message_text("⚠ ما لقيت الرابط، أرسل رابط يوتيوب من جديد.")
        return

    # 1) اختيار نوع التحميل
    if data.startswith("type:"):
        dl_type = data.split(":")[1]  # video أو audio
        user_data["dl_type"] = dl_type

        if dl_type == "video":
            # أزرار الجودة للفيديو
            kb = [
                [
                    InlineKeyboardButton("360p", callback_data="v_quality:360p"),
                    InlineKeyboardButton("480p", callback_data="v_quality:480p"),
                ],
                [
                    InlineKeyboardButton("720p", callback_data="v_quality:720p"),
                    InlineKeyboardButton("أعلى جودة", callback_data="v_quality:best"),
                ],
            ]
            await query.edit_message_text(
                "اختر جودة الفيديو:", reply_markup=InlineKeyboardMarkup(kb)
            )

        elif dl_type == "audio":
            kb = [
                [InlineKeyboardButton("🎧 أفضل جودة صوت", callback_data="a_quality:best")]
            ]
            await query.edit_message_text(
                "اختر جودة الصوت:", reply_markup=InlineKeyboardMarkup(kb)
            )

        return

    # 2) اختيار جودة الفيديو
    if data.startswith("v_quality:"):
        quality = data.split(":")[1]  # 360p / 480p / 720p / best
        await download_video(query, context, url, quality)
        return

    # 3) اختيار جودة الصوت
    if data.startswith("a_quality:"):
        quality = data.split(":")[1]  # حالياً بس best
        await download_audio(query, context, url, quality)
        return


# ========= تحميل الفيديو =========

async def download_video(query, context, url: str, quality: str):
    try:
        await query.edit_message_text("⏳ جاري فحص الفيديو…")

        yt = YouTube(url)

        # فحص مدة الفيديو
        duration_min = yt.length / 60
        if duration_min > MAX_DURATION_MIN:
            await query.edit_message_text(
                f"⚠ مدة الفيديو {int(duration_min)} دقيقة.\n"
                f"الحد الأقصى المسموح: {MAX_DURATION_MIN} دقيقة."
            )
            return

        # اختيار الستريم بناءً على الجودة
        if quality == "best":
            stream = yt.streams.filter(
                progressive=True, file_extension="mp4"
            ).get_highest_resolution()
        else:
            stream = yt.streams.filter(
                progressive=True, file_extension="mp4", res=quality
            ).first()
            if not stream:
                stream = yt.streams.filter(
                    progressive=True, file_extension="mp4"
                ).get_highest_resolution()

        if not stream:
            await query.edit_message_text("❌ ما قدرت ألقى ستريم مناسب للفيديو.")
            return

        await query.edit_message_text("⬇️ جاري تحميل الفيديو… (انتظر)")

        file_path = stream.download()
        file_size_mb = bytes_to_mb(os.path.getsize(file_path))

        if file_size_mb > MAX_FILE_SIZE_MB:
            os.remove(file_path)
            await query.edit_message_text(
                f"⚠ حجم الفيديو {file_size_mb:.1f} MB أكبر من الحد {MAX_FILE_SIZE_MB} MB."
            )
            return

        await query.edit_message_text("📤 جاري إرسال الفيديو…")

        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=open(file_path, "rb"),
            caption=f"{yt.title}\nالجودة: {stream.resolution}",
        )

        os.remove(file_path)

        await query.edit_message_text("✅ تم إرسال الفيديو بنجاح.")

    except Exception as e:
        await query.edit_message_text(f"❌ صار خطأ أثناء تحميل الفيديو:\n{e}")


# ========= تحميل الصوت =========

async def download_audio(query, context, url: str, quality: str):
    try:
        await query.edit_message_text("⏳ جاري فحص الفيديو…")

        yt = YouTube(url)

        duration_min = yt.length / 60
        if duration_min > MAX_DURATION_MIN:
            await query.edit_message_text(
                f"⚠ مدة الفيديو {int(duration_min)} دقيقة.\n"
                f"الحد الأقصى المسموح: {MAX_DURATION_MIN} دقيقة."
            )
            return

        await query.edit_message_text("⬇️ جاري تحميل الصوت… (انتظر)")

        # أفضل ستريم صوت
        stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()

        if not stream:
            await query.edit_message_text("❌ ما لقيت ستريم صوت مناسب.")
            return

        file_path = stream.download(filename_prefix="audio_")
        file_size_mb = bytes_to_mb(os.path.getsize(file_path))

        if file_size_mb > MAX_FILE_SIZE_MB:
            os.remove(file_path)
            await query.edit_message_text(
                f"⚠ حجم الصوت {file_size_mb:.1f} MB أكبر من الحد {MAX_FILE_SIZE_MB} MB."
            )
            return

        await query.edit_message_text("📤 جاري إرسال الصوت…")

        # أحياناً تيليجرام يدقّق على النوع، لو صار خطأ نرجع نرسله كـ document
        try:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(file_path, "rb"),
                title=yt.title,
                caption="🎧 تم استخراج الصوت من يوتيوب",
            )
        except Exception:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=open(file_path, "rb"),
                caption="🎧 تم استخراج الصوت من يوتيوب (ملف)",
            )

        os.remove(file_path)

        await query.edit_message_text("✅ تم إرسال الصوت بنجاح.")

    except Exception as e:
        await query.edit_message_text(f"❌ صار خطأ أثناء تحميل الصوت:\n{e}")


# ========= تشغيل البوت =========

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN غير مضبوط، حطّه في متغير بيئة أو داخل الكود.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # الهاندلرات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(buttons_handler))

    print("🚀 البوت يعمل الآن (Polling)…")
    app.run_polling()  # بدون asyncio.run وبدون await


if __name__ == "__main__":
    main()
