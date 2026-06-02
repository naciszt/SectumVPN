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
    
import aiohttp
from aiogram.types import BufferedInputFile

# ---------- safe send ----------
async def safe_send(message, text, limit=3500):
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        await message.answer(text[:cut], parse_mode="HTML")
        text = text[cut:]
    await message.answer(text, parse_mode="HTML")


# ---------- HTML REPORT ----------
def build_html(data, query):
    fast = data.get("fast-result", {})
    full = data.get("full-result", {})

    def esc(x):
        return str(x).replace("<", "&lt;").replace(">", "&gt;")

    html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ background:#0f0f0f; color:#eee; font-family:Arial; padding:20px; }}
        .box {{ background:#1c1c1c; padding:15px; border-radius:10px; margin-bottom:10px; }}
        .title {{ color:#4da3ff; font-size:20px; margin-bottom:10px; }}
        .item {{ margin:4px 0; }}
    </style>
    </head>
    <body>

    <div class="box">
        <div class="title">📊 OSINT REPORT</div>
        <div class="item">🔎 Query: <b>{esc(query)}</b></div>
    </div>

    <div class="box">
        <div class="title">⚡ Fast Result</div>
    """

    for k, v in fast.items():
        html += f"<div class='item'><b>{esc(k)}:</b> {esc(v)}</div>"

    html += """
    </div>

    <div class="box">
        <div class="title">📁 Full Result</div>
    """

    def walk(obj):
        nonlocal html
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ["source", "info_leak", "database"]:
                    continue
                html += f"<div class='item'><b>{esc(k)}:</b> {esc(v)}</div>"
        elif isinstance(obj, list):
            for i in obj:
                walk(i)
        else:
            html += f"<div class='item'>{esc(obj)}</div>"

    walk(full)

    html += "</div></body></html>"
    return html


# ---------- MAIN HANDLER ----------
@router.message(F.text)
async def handler(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            API_URL,
            params={"key": API_KEY, "search": message.text}
        ) as resp:
            try:
                data = await resp.json()
            except:
                await message.answer("❌ API error (not JSON / rate limit)")
                return

    if not data.get("success"):
        await message.answer("❌ Ничего не найдено")
        return

    search = data.get("search", "—")
    detected = data.get("detected_type", "—")
    results = data.get("results_count", 0)
    sources = data.get("sources_count", 0)
    time = data.get("search_time", "—")

    fast = data.get("fast-result", {})

    # ---------- TEXT (SHORT) ----------
    text = (
        f"📊 <b>Результат поиска</b>\n\n"
        f"🔎 <b>Запрос:</b> <code>{search}</code>\n"
        f"📌 <b>Тип:</b> {detected}\n\n"
        f"📦 <b>Результатов:</b> {results}\n"
        f"📚 <b>Источников:</b> {sources}\n"
        f"⏱ <b>Время:</b> {time}s\n\n"
        f"⚡ <b>Fast data:</b>\n"
    )

    # только полезное из fast-result
    for k, v in fast.items():
        text += f"• <b>{k}:</b> {v}\n"

    await safe_send(message, text)

    # ---------- HTML FILE ----------
    html = build_html(data, message.text)

    file = BufferedInputFile(
        html.encode("utf-8"),
        filename="report.html"
    )

    await message.answer_document(file, caption="📄 Полный отчёт (HTML)")

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
