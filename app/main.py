import os
import re
import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "988757303"))

# استخراج الرابط من الرسالة
def extract_url(text):
    url_pattern = r'(https?://[^\s]+)'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

# التعامل مع أي رسالة نصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    url = extract_url(message_text)

    if url:
        await update.message.reply_text(f"📥 تم استلام الرابط:\n{url}\nجاري التحميل...")

        # مثال: استخدام yt-dlp لتحميل الفيديو
        try:
            result = subprocess.run(
                ["yt-dlp", "-f", "best", "-o", "video.mp4", url],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                await update.message.reply_text("✅ تم تحميل الفيديو بنجاح (محلياً على السيرفر).")
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"📌 رابط جديد تم تحميله:\n{url}")
            else:
                await update.message.reply_text("❌ فشل التحميل، تحقق من الرابط أو نوع المحتوى.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطأ أثناء التحميل: {e}")
    else:
        await update.message.reply_text("📌 أرسل رابط وسيتم التعامل معه تلقائياً.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
