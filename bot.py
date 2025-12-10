import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from pytube import YouTube

# يفضّل تستخدم متغير بيئة على Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg")

# ========= أوامر أساسية =========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا 🙌\n"
        "أرسل رابط يوتيوب، وبعدها اختار نوع التحميل (فيديو/صوت) والجودة من الأزرار."
    )

# ========= التعامل مع الرابط =========

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # تأكد إنه رابط يوتيوب
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ أرسل رابط من YouTube فقط.")
        return

    # نخزن الرابط في user_data
    context.user_data["yt_url"] = url

    # أزرار اختيار نوع التحميل
    keyboard = [
        [
            InlineKeyboardButton("🎥 تحميل فيديو", callback_data="type:video"),
            InlineKeyboardButton("🎧 تحميل صوت", callback_data="type:audio"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "اختر نوع التحميل:", reply_markup=reply_markup
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
            # أزرار اختيار جودة الفيديو
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
                [
                    InlineKeyboardButton("أفضل جودة صوت 🎧", callback_data="a_quality:best"),
                ]
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

# ========= دوال التحميل =========

async def download_video(query, context, url: str, quality: str):
    await query.edit_message_text("⏳ جاري تجهيز الفيديو…")

    try:
        yt = YouTube(url)

        if quality == "best":
            stream = yt.streams.filter(progressive=True, file_extension="mp4").get_highest_resolution()
        else:
            stream = yt.streams.filter(progressive=True, file_extension="mp4", res=quality).first()
            # لو ما موجودة جودة معينة، نرجع لأعلى جودة متاحة
            if not stream:
                stream = yt.streams.filter(progressive=True, file_extension="mp4").get_highest_resolution()

        if not stream:
            await query.edit_message_text("❌ ما قدرت ألقى ستريم مناسب للفيديو.")
            return

        file_path = stream.download()

        await query.edit_message_text("📤 جاري إرسال الفيديو…")

        # إرسال كفيديو
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=open(file_path, "rb"),
            caption=f"{yt.title}\nالجودة: {stream.resolution}",
        )

        os.remove(file_path)

    except Exception as e:
        await query.edit_message_text(f"❌ صار خطأ أثناء تحميل الفيديو:\n{e}")

async def download_audio(query, context, url: str, quality: str):
    await query.edit_message_text("⏳ جاري تجهيز الصوت…")

    try:
        yt = YouTube(url)

        # أفضل ستريم صوت متاح
        stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()

        if not stream:
            await query.edit_message_text("❌ ما لقيت ستريم صوت مناسب.")
            return

        file_path = stream.download(filename_prefix="audio_")

        await query.edit_message_text("📤 جاري إرسال الصوت…")

        # نرسل كـ Audio أو Document (بعض الأحيان يكون WebM أو MP4)
        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=open(file_path, "rb"),
            title=yt.title,
            caption="🎧 صوت من يوتيوب",
        )

        os.remove(file_path)

    except Exception as e:
        await query.edit_message_text(f"❌ صار خطأ أثناء تحميل الصوت:\n{e}")

# ========= تشغيل البوت =========

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠ رجاءً حدد BOT_TOKEN كمتغير بيئة أو داخل الكود.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(buttons_handler))

    print("✅ البوت يعمل الآن (Polling)…")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
