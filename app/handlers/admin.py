from aiogram import Router, types

router = Router()

@router.message(lambda m: m.text == "📊 الإحصائيات")
async def stats(message: types.Message):
    await message.answer(
        "📊 الحالة: تعمل ✅\n"
        "💾 الذاكرة: خفيفة\n"
        "📨 الطلبات: منخفضة"
    )

@router.message(lambda m: m.text == "⚙️ الإعدادات")
async def settings(message: types.Message):
    kb = [
        [types.KeyboardButton(text="🔒 تغيير كلمة السر")],
        [types.KeyboardButton(text="⬅️ رجوع")]
    ]
    await message.answer(
        "⚙️ إعدادات البوت:\nاختر من القائمة:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
