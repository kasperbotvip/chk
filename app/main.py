import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "988757303"))

# دالة تتحقق من وجود رابط في الرسالة
def extract_url(text):
    url_pattern = r'(https?://[^\s]+)'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

# الرد التلقائي على أي رسالة تحتوي رابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    url = extract_url(message_text)

    if url:
        await update.message.reply_text(f"📥 تم استلام الرابط:\n{url}\nجاري التحميل...")
        # هنا تقدر تضيف كود التحميل أو المعالجة حسب نوع الرابط
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔗 رابط جديد من @{update.effective_user.username or 'مستخدم'}:\n{url}")
    else:
        await update.message.reply_text("📌 أرسل رابط وسيتم التعامل معه تلقائياً.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
