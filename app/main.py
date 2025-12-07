import os
import re
import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "988757303"))

def extract_url(text):
    url_pattern = r'(https?://[^\s]+)'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    url = extract_url(message_text)

    if url:
        await update.message.reply_text(f"📥 تم استلام الرابط:\n{url}\nجاري التحميل...")

        try:
            # تحميل الفيديو باستخدام yt-dlp
            subprocess.run([
                "yt-dlp",
                "-f", "mp4",
                "-o", "video.mp4",
                url
            ], check=True)

            # إرسال الفيديو للمستخدم
            with open("video.mp4", "rb") as video_file:
                await update.message.reply_video(video=video_file, caption="✅ تم تحميل الفيديو وإرساله بنجاح.")

            # إشعار للـ Admin
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📦 تم إرسال فيديو من الرابط:\n{url}")

        except Exception as e:
            await update.message.reply_text(f"❌ فشل التحميل أو الإرسال: {e}")
    else:
        await update.message.reply_text("📌 أرسل رابط وسيتم تحميل الفيديو تلقائياً.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
