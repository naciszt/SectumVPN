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

import aiohttp

# ---------- helpers ----------

def clean_list(data):
    """[['type','value']] -> unique values"""
    if not isinstance(data, list):
        return []

    out = []
    for item in data:
        if isinstance(item, list) and len(item) == 2:
            val = str(item[1]).strip()
            if val and val not in out:
                out.append(val)
    return out


def split_text(text, limit=3500):
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def build_report(data: dict) -> str:
    fast = data.get("fast-result", {}) or {}
    full = data.get("full-result", {}) or {}

    search = data.get("search", "—")
    detected = data.get("detected_type", "unknown")
    results_count = data.get("results_count", 0)
    sources_count = data.get("sources_count", 0)
    time = data.get("search_time", "—")

    # FAST DATA
    phone = clean_list(fast.get("phone"))
    email = clean_list(fast.get("email"))
    fullname = clean_list(fast.get("fullname"))
    region = clean_list(fast.get("region"))
    country = clean_list(fast.get("country"))

    # BASE INFO
    base = full.get("Базовая информация", {}) if isinstance(full.get("Базовая информация"), dict) else {}

    text = (
        f"📊 <b>РЕЗУЛЬТАТ ПОИСКА</b>\n\n"
        f"🔎 <b>Запрос:</b> <code>{search}</code>\n"
        f"📌 <b>Тип:</b> {detected}\n\n"
        f"🌍 <b>Страна:</b> {country[0] if country else '—'}\n"
        f"🗺 <b>Регион:</b> {region[0] if region else '—'}\n\n"
        f"📦 <b>Результатов:</b> {results_count}\n"
        f"📚 <b>Источников:</b> {sources_count}\n"
        f"⏱ <b>Время:</b> {time}s\n"
    )

    # FAST BLOCK
    text += "\n📁 <b>БЫСТРЫЕ ДАННЫЕ</b>\n"

    if fullname:
        text += f"👤 <b>Имя:</b> {', '.join(fullname)}\n"
    if phone:
        text += f"📞 <b>Телефон:</b> {', '.join(phone)}\n"
    if email:
        text += f"📧 <b>Email:</b> {', '.join(email)}\n"

    # BASE INFO CLEAN
    if base:
        text += "\n📍 <b>БАЗОВАЯ ИНФОРМАЦИЯ</b>\n"
        for k, v in base.items():
            text += f"• {k}: {v}\n"

    # DB DATA CLEAN
    dbs = full.get("Базы Данных", [])
    if not isinstance(dbs, list):
        dbs = []

    text += "\n📦 <b>ДАННЫЕ ИЗ БАЗ</b>\n"

    seen = set()
    count = 0

    for db in dbs:
        if not isinstance(db, dict):
            continue

        source = db.get("source", "unknown")
        info = db.get("info_leak", "") or db.get("description", "") or ""

        info_clean = str(info).strip()

        if not info_clean or info_clean in seen:
            continue

        seen.add(info_clean)
        count += 1

        text += f"\n🔹 <b>{count}. {source}</b>\n{info_clean}\n"

        if count >= 10:
            break

    return text
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
