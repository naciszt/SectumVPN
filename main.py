# ---------- by whoami @naciszt & lozes @cykalozes ----------
import asyncio

from collections import defaultdict
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import as  noMessage, CallbackQuery, BufferedInputFile
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from config import TOKEN
banner = FSInputFile("banner.jpeg")

MAINTOKEN = TOKEN

@dp.message(CommandStart)
async def start(message: types.Message):
  id = message.from_user.id

  kb = InlineKeyboardBuilder()
  kb.button(text="<tg-emoji emoji-id="5425144049671627237">🐸</tg-emoji> Аренда")
  kb.adjust(1)

  await message.answer_photo(photo=banner, captionf="""[<tg-emoji emoji-id="5330437392274827570">🧛</tg-emoji>] <b>Главное Меню</b> — Лучший и самый дешевый бот аренды NFT!

<tg-emoji emoji-id="5454134258580877567">💳</tg-emoji> <b>Текущий баланс</b> — {balance}

<tg-emoji emoji-id="5308022477648056652">😎</tg-emoji> <i>Выберите действие</i>:""", reply_markup=kb.as_markup())

async def main():
  main_bot = Bot(
        MAIN_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
  main_dp = Dispatcher()
  main_router = make_router(is_mirror=False)
  main_dp.include_router(main_router)
  
  print(f"[🔍] Бот запущен")
  await main_dp.start_polling(main_bot)

if __name__ == "__main__":
  asyncio.run(main())
