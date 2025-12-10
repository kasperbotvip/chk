import logging
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل رابط من إنستغرام (ستوريات/ريلز/صور) أو تيك توك، وأنا أحمله لك 🎬📸"
    )

# دالة التحميل العامة
def download_media(url: str) -> str:
    ydl_opts = {
        "outtmpl": "download.%(ext)s",
        "format": "best",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# التعامل مع أي رابط
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text("جاري التحميل... ⏳")

    try:
        file_path = download_media(url)
        if file_path.endswith((".jpg", ".png")):
            await update.message.reply_photo(photo=open(file_path, "rb"))
        else:
            await update.message.reply_video(video=open(file_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحميل: {e}")

def main():
    # ضع التوكن هنا
    app = Application.builder().token("5788330295:AAH3OJMoXFukkprXF1L_EesqduP4_VZSCCA").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    app.run_polling()

if __name__ == "__main__":
    main()
