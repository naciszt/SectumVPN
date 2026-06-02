# ---------- by whoami @naciszt ----------
import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
        kb.button(text="🏴‍☠️ Подписаться", url="https://t.me/+O3Nsqbyb6c8zMzli")
        kb.button(text="✅ Проверить", callback_data="checksub")
        
        await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="🔥 Для использование бота подпишитесь на наши телеграм каналы:)\n\n@kildoxer", reply_markup=kb.as_markup())
        return
    await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="""<b>💎 Kildoxer Info</b>

<i>Пока-что доступен только поиск по номеру, для поиска напиши номер в таком формате: <code>+79ХХХХХХХХХ</code></i>

<b>Наш телеграм канал: @kildoxer</b>""", parse_mode="HTML")

def clean_text(text: str) -> str:
    return (
        text.replace("<em>", "")
            .replace("</em>", "")
            .strip()
    )
    
@router.message(F.text)
async def handler(message: Message):
    if not await checksubi(
        message.bot,
        message.from_user.id,
        tgk
      ):
        kb = InlineKeyboardBuilder()
        kb.button(text="🏴‍☠️ Подписаться", url="https://t.me/+O3Nsqbyb6c8zMzli")
        kb.button(text="✅ Проверить", callback_data="checksub")
        
        await message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="🔥 Для использование бота подпишитесь на наши телеграм каналы:)\n\n@kildoxer", reply_markup=kb.as_markup())
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(
            API_URL,
            params={
                "key": API_KEY,
                "search": message.text
            }
        ) as resp:
            data = await resp.json()
    if not data.get("success"):
        await message.answer("❌ Ничего не найдено")
        return
    search = data.get("search", "—")
    detected = data.get("detected_type", "unknown")
    results_count = data.get("results_count", 0)
    sources_count = data.get("sources_count", 0)
    time = data.get("search_time", "—")
    fast = data.get("fast-result", {})
    full = data.get("full-result", {})
    country = "—"
    region = "—"
    if isinstance(fast.get("country"), list) and fast["country"]:
        country = fast["country"][0][1]
    if isinstance(fast.get("region"), list) and fast["region"]:
        region = fast["region"][0][1]

    text = (
        f"📊 <b>Результат поиска</b>\n\n"
        f"🔎 <b>Запрос:</b> <code>{search}</code>\n"
        f"📌 <b>Тип:</b> {detected}\n\n"
        f"🌍 <b>Страна:</b> {country}\n"
        f"🗺 <b>Регион:</b> {region}\n\n"
        f"📦 <b>Результатов:</b> {results_count}\n"
        f"📚 <b>Источников:</b> {sources_count}\n"
        f"⏱ <b>Время:</b> {time}s\n"
    )
    dbs = full.get("Базы Данных", [])
    if dbs:
        text += "\n📁 <b>Результаты из баз:</b>\n
        for i, db in enumerate(dbs, 1):
            info = db.get("info_leak", "")

            clean = clean_text(info)

        # пропускаем пустые / мусор
            if not clean or "No results found" in clean:
                continue

            text += f"\n<b>{i}. Результат:</b>\n{clean}\n"
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data == "checksub")
async def checksub(callback: CallbackQuery):
    if not await checksubi(callback.bot, callback.from_user.id, tgk):

        kb = InlineKeyboardBuilder()
        kb.button(text="🏴‍☠️ Подписаться", url="https://t.me/+O3Nsqbyb6c8zMzli")
        kb.button(text="✅ Проверить", callback_data="checksub")

        await callback.message.answer_photo(
            photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg",
            caption="Ты не подписался!",
            reply_markup=kb.as_markup()
        )
        return
    await callback.message.answer_photo(photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg", caption="""<b>💎 Kildoxer Info</b>

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
