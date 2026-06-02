# ---------- by whoami @naciszt ----------
import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
router = Router()

API_URL = "http://cryven.info/api/search"
API_KEY = "@naciszt:9qVZfRS4"

TOKEN = "8990718691:AAFZw7IL59sKmH0--JCaAgMtYmz4aYr77FY"

tgk = [-1002488180084]

async def checksubi(bot, user_id: int, channels: list[int]) -> bool:
    for ch in tgk:
        member = await bot.get_chat_member(ch, user_id)
        if member.status in ["left", "kicked"]:
            return False
    return True

def flatten_json(data, prefix=""):
    lines = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_prefix = f"{prefix}{k}: "
            lines.extend(flatten_json(v, new_prefix))
    elif isinstance(data, list):
        for item in data:
            lines.extend(flatten_json(item, prefix))
    else:
        lines.append(f"{prefix}{data}")
    return lines

@router.message(Command("start"))
async def start(message: Message):
    if not await checksubi(
        message.bot,
        message.from_user.id,
        tgk
      ):
        kb = InlineKeyboardBuilder()
        kb.button(text="🏴‍☠️ Подписаться", url="t.me/xblogwin")
        kb.button(text="✅ Проверить", callback_data="checksub")
        
        await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="🔥 Для использование бота подпишитесь на наши телеграм каналы:)\n\n@kildoxer", reply_markup=kbb.as_markup())
        return
    await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="""<b>💎 Kildoxer Info</b>

<i>Пока-что доступен только поиск по номеру, для поиска напиши номер в таком формате: <code>+79ХХХХХХХХХ</code></i>

<b>Наш телеграм канал: @kildoxer</b>""", parse_mode="HTML")

@router.message(F.text)
async def handler(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            API_URL,
            params={"key": API_KEY, "search": message.text}
        ) as resp:
            data = await resp.json()
    if not data.get("success"):
        await message.answer("❌ Ничего не найдено")
        return
    lines = flatten_json(data)
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > 3500:
            await message.answer(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await message.answer(chunk)

@router.callback_query(F.data == "checksub")
async def checksub(callback: CallbackQuery):
    if not await checksubi(
        message.bot,
        message.from_user.id,
        tgk
      ):
        kb = InlineKeyboardBuilder()
        kb.button(text="🏴‍☠️ Подписаться", url="t.me/+ccvOpqglLwplYjli")
        kb.button(text="✅ Проверить", callback_data="checksub")

        await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="🔥 Для использование бота подпишитесь на наш телеграм канал:)\n\n@kildoxer", reply_markup=kbb.as_markup())
        return
    await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="""<b>💎 Kildoxer Info</b>

<i>Пока-что доступен только поиск по номеру, для поиска напиши номер в таком формате: <code>+79ХХХХХХХХХ</code></i>

<b>Наш телеграм канал: @kildoxer</b>""", parse_mode="HTML")

async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
