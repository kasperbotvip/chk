import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# القيم من البيئة أو مباشرة
BOT_TOKEN = os.getenv("BOT_TOKEN", "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "988757303"))

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅")

# أمر /ping يرسل للـ Admin
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=ADMIN_ID, text="Ping من البوت 🚀")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping))

    # تشغيل البوت بالـ Polling
    application.run_polling()

if __name__ == "__main__":
    main()
