from aiogram import Router, types

router = Router()

@router.message(lambda m: m.text == "📝 إيكو")
async def prompt_echo(message: types.Message):
    await message.answer("أرسل لي أي نص لأعيده لك.")

@router.message()
async def echo(message: types.Message):
    if message.text:
        await message.answer(f"إيكو: {message.text[:4096]}")
