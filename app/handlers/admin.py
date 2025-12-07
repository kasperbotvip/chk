from aiogram import Router, types
from aiogram.filters import Text
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold

router = Router()
storage = MemoryStorage()

@router.message(Text("📊 الإحصائيات"))
async def stats(message: types.Message):
    # مثال مبسط — يمكنك ربطه بقاعدة بيانات لاحقاً
    await message.answer(f"{hbold('الحالة')}: تعمل ✅\nالذاكرة: خفيفة\nطلبات: منخفضة")
