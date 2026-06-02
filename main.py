# ---------- by whoami @naciszt ----------
import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message

router = Router()

API_URL = "http://cryven.info/api/search"
API_KEY = "@naciszt:9qVZfRS4"

TOKEN = "8990718691:AAFZw7IL59sKmH0--JCaAgMtYmz4aYr77FY"

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

    # Telegram лимит 4096 символов — режем аккуратно

    chunk = ""

    for line in lines:

        if len(chunk) + len(line) + 1 > 3500:

            await message.answer(chunk)

            chunk = ""

        chunk += line + "\n"

    if chunk:

        await message.answer(chunk)
async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
