# ---------- by whoami @naciszt ----------
import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message

router = Router()

API_URL = "http://cryven.info/api/search"
API_KEY = "@naciszt:9qVZfRS4"

TOKEN = "8990718691:AAFZw7IL59sKmH0--JCaAgMtYmz4aYr77FY"

@router.message(F.text)
async def handler(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            API_URL,
            params={"key": API_KEY, "search": message.text}
        ) as resp:
            data = await resp.json()

    await message.answer(str(data))

async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
