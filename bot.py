import os
import time
import uuid
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from moviepy.editor import VideoFileClip

# التوكن من متغير البيئة (على Render حطه كـ BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAFOQZWDUTw80xSB_4TPxfRQ5Hl_xhj1tF4")

# حماية بسيطة من السبام
RATE_LIMIT_SECONDS = 20  # كل مستخدم ينتظر 20 ثانية بين كل تحويل
user_last_request = {}


def check_rate_limit(user_id: int) -> int:
    """
    يرجّع كم ثانية باقي لو المستخدم عدّه سبام،
    ولو 0 معناها مسموح.
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
        "هلا بيك 🙌\n"
        "أنا بوت يحوّل الفيديو إلى صوت (MP3) 🎧\n\n"
        "▫️ فقط أرسل لي فيديو (كـ فيديو عادي أو ملف)\n"
        "▫️ راح أرجع لك الصوت المستخرج من الفيديو."
    )


# ========= التعامل مع الفيديوهات =========

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user_id = message.from_user.id

    # حماية سبام خفيفة
    wait_sec = check_rate_limit(user_id)
    if wait_sec > 0:
        await message.reply_text(
            f"⏳ رجاءً انتظر {wait_sec} ثانية قبل طلب جديد."
        )
        return

    # نحدد هل هو فيديو عادي أو ملف فيديو
    tg_file = None
    file_name = None

    if message.video:
        tg_file = await message.video.get_file()
        file_name = message.video.file_name or "video.mp4"
    elif message.document and message.document.mime_type and "video" in message.document.mime_type:
        tg_file = await message.document.get_file()
        file_name = message.document.file_name or "video.mp4"
    else:
        await message.reply_text("❌ أرسل فيديو كـ رسالة فيديو أو ملف فيديو.")
        return

    await message.reply_text("⬇️ استلمت الفيديو، جاري التحويل إلى صوت… انتظر شوي 🎧")

    # مسارات مؤقتة
    unique_id = uuid.uuid4().hex
    input_path = f"input_{unique_id}.mp4"
    output_path = f"audio_{unique_id}.mp3"

    try:
        # تحميل الملف من تيليجرام إلى السيرفر
        await tg_file.download_to_drive(input_path)

        # استخدام moviepy لاستخراج الصوت
        video_clip = VideoFileClip(input_path)

        if video_clip.audio is None:
            await message.reply_text("❌ هذا الفيديو لا يحتوي على مسار صوت.")
            video_clip.close()
            os.remove(input_path)
            return

        # كتابة الصوت إلى ملف MP3
        video_clip.audio.write_audiofile(output_path, verbose=False, logger=None)
        video_clip.close()

        # إرسال الصوت للمستخدم
        await message.reply_text("📤 تم استخراج الصوت، جاري الإرسال…")

        with open(output_path, "rb") as audio_file:
            # نستخدم send_audio حتى يظهر كملف صوت
            await context.bot.send_audio(
                chat_id=message.chat_id,
                audio=audio_file,
                title=file_name,
                caption="🎧 هذا الصوت المستخرج من الفيديو."
            )

        await message.reply_text("✅ تم الإرسال بنجاح.")

    except Exception as e:
        # لو صار خطأ نطبع نصه حتى تقدر تشوفه
        await message.reply_text(f"❌ صار خطأ أثناء التحويل:\n{e}")
    finally:
        # تنظيف الملفات المؤقتة
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass


# ========= تشغيل البوت =========

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN غير مضبوط، حطّه بمتغير بيئة أو داخل الكود.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # استقبال الفيديوهات (video أو document/video)
    video_filter = filters.VIDEO | (filters.Document.VIDEO)
    app.add_handler(MessageHandler(video_filter, handle_video))

    print("🚀 البوت يعمل الآن (Polling)…")
    app.run_polling()


if __name__ == "__main__":
    main()
