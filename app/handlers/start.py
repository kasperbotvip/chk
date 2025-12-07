from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def on_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="📊 الإحصائيات"), types.KeyboardButton(text="⚙️ الإعدادات")],
        [types.KeyboardButton(text="📝 إيكو")]
    ]
    await message.answer(
        "أهلاً بك! هذا بوت جاهز للنشر على Render.\nاختر من الأزرار:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
