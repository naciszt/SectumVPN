import asyncio
import requests
import re

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
import aiohttp
from aiogram import Router, F
from aiogram.types import Message

router = Router()

API_URL = "https://api.cryven.info/v1/chat"
API_KEY = "@naciszt:9qVZfRS4"
TOKEN = "8990718691:AAFZw7IL59sKmH0--JCaAgMtYmz4aYr77FY"

@router.message(F.text)
async def handler(message: Message):
    async with aiohttp.ClientSession() as session:
        payload = {
            "message": message.text
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        async with session.post(API_URL, json=payload, headers=headers) as resp:
            data = await resp.json()

    answer = data.get("response", "нет ответа")

    await message.answer(answer)

async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
