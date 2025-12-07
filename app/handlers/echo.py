from aiogram import Router, types
from aiogram.filters import Text

router = Router()

@router.message(Text("📝 إيكو"))
async def prompt_echo(message: types.Message):
    await message.answer("أرسل لي أي نص لأعيده لك.")

@router.message()
async def echo(message: types.Message):
    # إيكو بسيط مع حماية من الميديا الثقيلة
    if message.text:
        await message.answer(f"إيكو: {message.text[:4096]}")
