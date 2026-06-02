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
    if not await checksubi(message.bot, message.from_user.id, tgk):
        kb = InlineKeyboardBuilder()
        kb.button(text="🏴‍☠️ Подписаться", url="https://t.me/+O3Nsqbyb6c8zMzli")
        kb.button(text="✅ Проверить", callback_data="checksub")

        await message.answer_photo(
            photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg",
            caption="Подпишись сначала.",
            reply_markup=kb.as_markup()
        )
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(
            API_URL,
            params={"key": API_KEY, "search": message.text}
        ) as resp:

            # защита от 429 / html
            try:
                data = await resp.json()
            except:
                await message.answer("❌ API не ответило JSON (429/ошибка)")
                return

    if not data.get("success"):
        await message.answer("❌ Ничего не найдено")
        return

    search = data.get("search", "—")
    detected = data.get("detected_type", "—")

    fast = data.get("fast-result", {})
    full = data.get("full-result", {})

    # --------- базовые поля ---------
    country = "—"
    region = "—"
    email = "—"
    phone = "—"
    fullname = "—"

    def extract(obj):
        nonlocal country, region, email, phone, fullname

        if isinstance(obj, dict):
            for k, v in obj.items():
                extract(v)

        elif isinstance(obj, list):
            for i in obj:
                extract(i)

        elif isinstance(obj, str):
            val = obj.strip()

            if "@" in val:
                email = val
            elif val.startswith("+") or val.isdigit():
                phone = val
            elif val.lower() in ["россия", "russia"]:
                country = val
            elif "европа" in val.lower() or "регион" in val.lower():
                region = val
            elif len(val.split()) <= 3:
                fullname = val

    extract(fast)

    # --------- результат ---------
    text = (
        f"📊 <b>Результат поиска</b>\n\n"
        f"🔎 <b>Запрос:</b> <code>{search}</code>\n"
        f"📌 <b>Тип:</b> {detected}\n\n"
        f"🌍 <b>Страна:</b> {country}\n"
        f"🗺 <b>Регион:</b> {region}\n\n"
        f"📧 <b>Email:</b> {email}\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"👤 <b>Имя:</b> {fullname}\n"
    )

    # --------- чистый full-result (без бд-шумa) ---------
    values = set()

    def collect(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                collect(v)
        elif isinstance(obj, list):
            for i in obj:
                collect(i)
        else:
            s = str(obj).strip()

            # фильтр мусора
            if any(x in s.lower() for x in ["source", "info_leak", "database"]):
                return

            if len(s) > 2:
                values.add(s)

    collect(full)

    if values:
        text += "\n📁 <b>Данные:</b>\n"
        for v in list(values)[:15]:  # ограничение
            text += f"• {v}\n"

    # --------- защита от лимита telegram ---------
    for i in range(0, len(text), 3500):
        await message.answer(text[i:i+3500], parse_mode="HTML")
        
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
