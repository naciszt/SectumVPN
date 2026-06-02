# ---------- by whoami @naciszt ----------
import asyncio
import aiohttp
import re
import html as html_module
import json
import os
from datetime import datetime
from collections import defaultdict

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

banner = FSInputFile("banner.jpeg")
# ═══════════════════════════════════════════════
#  КОНФИГ
# ═══════════════════════════════════════════════
MAIN_TOKEN   = "8990718691:AAFZw7IL59sKmH0--JCaAgMtYmz4aYr77FY"
API_URL      = "http://cryven.info/api/search"
API_KEY      = "@naciszt:9qVZfRS4"
SUB_CHANNELS = [-1002488180084]          # каналы для проверки подписки
ADMIN_IDS    = {8317444646, 1768487973}
DATA_FILE    = "bot_data.json"           # файл хранения данных

# ═══════════════════════════════════════════════
#  ХРАНИЛИЩЕ (JSON-файл, чтобы пережить рестарт)
# ═══════════════════════════════════════════════
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"mirrors": [], "banned": [], "limits": {}, "users": {}}

def save_data(d: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

DB = load_data()
# mirrors  — список {"token": "...", "label": "..."}
# banned   — список user_id (int)
# limits   — {str(uid): int}  0 = заблокированы запросы
# users    — {str(uid): {stats}}

# ═══════════════════════════════════════════════
#  ЗЕРКАЛА — запущенные экземпляры
# ═══════════════════════════════════════════════
mirror_tasks: dict[str, asyncio.Task] = {}   # token -> Task
mirror_bots:  dict[str, Bot]          = {}   # token -> Bot

# ═══════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ
# ═══════════════════════════════════════════════
SEARCH_TYPES = {
    "phone":    ("📞", "Телефон",   "Пример: 79991234567"),
    "email":    ("📧", "Email",     "Пример: user@mail.ru"),
    "fio":      ("👤", "ФИО",       "Пример: Иванов Иван Иванович"),
    "vk":       ("💙", "VK",        "Пример: id123456 или @nick"),
    "telegram": ("✈️", "Telegram",  "Пример: @username"),
    "ip":       ("🌐", "IP",        "Пример: 1.2.3.4"),
    "snils":    ("📄", "СНИЛС",     "Пример: 123-456-789 00"),
    "inn":      ("🏦", "ИНН",       "Пример: 123456789012"),
    "car":      ("🚗", "Авто",      "Пример: А123БВ777"),
    "nick":     ("🎮", "Ник",       "Пример: username"),
}

user_search_type: dict[int, str] = {}   # uid -> type_key
admin_state:      dict[int, str] = {}   # uid -> pending action

def esc(v) -> str:
    return html_module.escape(str(v) if v is not None else "")

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def is_banned(uid: int) -> bool:
    return uid in DB.get("banned", [])

def get_limit(uid: int):
    """None = безлимит, int = осталось запросов."""
    lim = DB.get("limits", {}).get(str(uid))
    return lim  # None если нет записи

def use_request(uid: int) -> bool:
    """Возвращает True если запрос разрешён, уменьшает счётчик."""
    lim = DB["limits"].get(str(uid))
    if lim is None:
        return True
    if lim <= 0:
        return False
    DB["limits"][str(uid)] -= 1
    save_data(DB)
    return True

def get_or_create_user(uid: int) -> dict:
    key = str(uid)
    if key not in DB["users"]:
        DB["users"][key] = {
            "requests": 0,
            "first_seen": datetime.now().isoformat(),
            "last_request": None,
            "last_query": None,
            "logs": []
        }
        save_data(DB)
    return DB["users"][key]

def update_user_stat(uid: int, search_type: str, query: str):
    u = get_or_create_user(uid)
    now = datetime.now()
    u["requests"] += 1
    u["last_request"] = now.isoformat()
    u["last_query"] = query
    u["logs"].append(f"[{now.strftime('%d.%m %H:%M')}] {search_type}: {query[:40]}")
    if len(u["logs"]) > 20:
        u["logs"] = u["logs"][-20:]
    save_data(DB)

# ═══════════════════════════════════════════════
#  ПРОВЕРКА ПОДПИСКИ (через основной бот)
# ═══════════════════════════════════════════════
_main_bot_ref: Bot | None = None

async def checksubi(user_id: int) -> bool:
    """Всегда проверяем через ОСНОВНОЙ бот."""
    bot = _main_bot_ref
    if bot is None:
        return True
    for ch in SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            pass
    return True

# ═══════════════════════════════════════════════
#  ОЧИСТКА ДАННЫХ
# ═══════════════════════════════════════════════
def clean_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(p for p in (clean_value(v) for v in value) if p)
    if isinstance(value, dict):
        return ", ".join(p for p in (clean_value(v) for v in value.values()) if p)
    s = str(value)
    s = re.sub(r'[\[\]{}"\'\\]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def to_str_list(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            v = clean_value(item)
            if v and v not in result:
                result.append(v)
        return result
    v = clean_value(value)
    return [v] if v else []

# ═══════════════════════════════════════════════
#  HTML ОТЧЁТ
# ═══════════════════════════════════════════════
def build_html_report(data: dict, query: str, search_type: str) -> str:
    fast = data.get("fast-result") or {}
    if not isinstance(fast, dict): fast = {}
    full = data.get("full-result") or {}
    if not isinstance(full, dict): full = {}

    detected      = data.get("detected_type", search_type) or search_type
    results_count = data.get("results_count", 0)
    sources_count = data.get("sources_count", 0)
    search_time   = data.get("search_time", "—")

    phone    = to_str_list(fast.get("phone"))
    email    = to_str_list(fast.get("email"))
    fullname = to_str_list(fast.get("fullname") or fast.get("name") or fast.get("fio"))
    region   = to_str_list(fast.get("region"))
    country  = to_str_list(fast.get("country"))

    base_info = full.get("Базовая информация") or {}
    if not isinstance(base_info, dict): base_info = {}
    dbs = full.get("Базы Данных") or []
    if not isinstance(dbs, list): dbs = []

    FAST_KNOWN = {
        "fullname": ("👤 ФИО",     fullname),
        "phone":    ("📞 Телефон", phone),
        "email":    ("📧 Email",   email),
        "region":   ("🗺 Регион",  region),
        "country":  ("🌍 Страна",  country),
    }
    skip_in_extra = set(FAST_KNOWN.keys()) | {"name", "fio"}

    fast_rows = ""
    for label, vals in FAST_KNOWN.values():
        if vals:
            fast_rows += f"<tr><td>{label}</td><td>{esc(', '.join(vals))}</td></tr>\n"
    for k, v in fast.items():
        if k in skip_in_extra: continue
        cleaned = clean_value(v)
        if cleaned:
            fast_rows += f"<tr><td>{esc(k)}</td><td>{esc(cleaned)}</td></tr>\n"

    base_rows = ""
    for k, v in base_info.items():
        cleaned = clean_value(v)
        if cleaned:
            base_rows += f"<tr><td>{esc(k)}</td><td>{esc(cleaned)}</td></tr>\n"

    leaks_html = ""
    for idx, db in enumerate(dbs, 1):
        if not isinstance(db, dict): continue
        source = clean_value(
            db.get("source") or db.get("database") or db.get("name") or db.get("db") or f"Источник {idx}"
        )
        fields_html = ""
        for k, v in db.items():
            if k in ("source", "database", "db"): continue
            cleaned = clean_value(v)
            if cleaned:
                fields_html += f"<tr><td>{esc(k)}</td><td>{esc(cleaned)}</td></tr>\n"
        if fields_html:
            leaks_html += f"""<div class="leak-block">
  <div class="leak-title">🔹 {idx}. {esc(source)}</div>
  <table>{fields_html}</table>
</div>\n"""

    if not leaks_html:  leaks_html = '<p class="empty">Записей из баз не найдено</p>'
    if not fast_rows:   fast_rows  = '<tr><td colspan="2" class="empty">Нет данных</td></tr>'
    if not base_rows:   base_rows  = '<tr><td colspan="2" class="empty">Нет данных</td></tr>'

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    return f"""<!DOCTYPE html><html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Досье KilDoxer — {esc(query)}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d0d0d;color:#e0e0e0;font-family:'Courier New',monospace;padding:24px}}
.header{{border:1px solid #333;border-radius:8px;padding:20px 24px;margin-bottom:24px;background:#111}}
.header h1{{font-size:22px;color:#fff;margin-bottom:12px;letter-spacing:2px}}
.meta-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:12px}}
.meta-item{{background:#1a1a1a;border-radius:6px;padding:10px 14px;border-left:3px solid #444}}
.meta-item .label{{font-size:11px;color:#888;margin-bottom:4px}}
.meta-item .value{{font-size:14px;color:#fff;word-break:break-all}}
.section{{margin-bottom:24px}}
.section-title{{font-size:14px;letter-spacing:1px;color:#aaa;text-transform:uppercase;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #222}}
table{{width:100%;border-collapse:collapse}}
td{{padding:8px 12px;border-bottom:1px solid #1e1e1e;font-size:13px;vertical-align:top}}
td:first-child{{color:#888;width:35%;font-size:12px}}
td:last-child{{color:#e0e0e0;word-break:break-all}}
tr:hover td{{background:#161616}}
.leak-block{{background:#111;border:1px solid #2a2a2a;border-radius:8px;margin-bottom:14px;overflow:hidden}}
.leak-title{{background:#1a1a1a;padding:10px 16px;font-size:13px;color:#ccc;font-weight:bold;border-bottom:1px solid #222}}
.empty{{color:#555;font-size:13px;padding:10px}}
.footer{{text-align:center;color:#333;font-size:12px;margin-top:32px;padding-top:16px;border-top:1px solid #1e1e1e}}
</style></head><body>
<div class="header"><h1>◈ KILDOXER REPORT</h1>
<div class="meta-grid">
<div class="meta-item"><div class="label">Запрос</div><div class="value">{esc(query)}</div></div>
<div class="meta-item"><div class="label">Тип</div><div class="value">{esc(detected)}</div></div>
<div class="meta-item"><div class="label">Результатов</div><div class="value">{esc(results_count)}</div></div>
<div class="meta-item"><div class="label">Источников</div><div class="value">{esc(sources_count)}</div></div>
<div class="meta-item"><div class="label">Время</div><div class="value">{esc(search_time)}s</div></div>
<div class="meta-item"><div class="label">Дата</div><div class="value">{now}</div></div>
</div></div>
<div class="section"><div class="section-title">⚡ Быстрые данные</div>
<div class="leak-block"><table>{fast_rows}</table></div></div>
<div class="section"><div class="section-title">📍 Базовая информация</div>
<div class="leak-block"><table>{base_rows}</table></div></div>
<div class="section"><div class="section-title">📦 Данные из утечек</div>{leaks_html}</div>
<div class="footer">Сгенерировано ботом KilDoxer · {now}</div>
</body></html>"""

# ═══════════════════════════════════════════════
#  КЛАВИАТУРЫ
# ═══════════════════════════════════════════════
def main_keyboard(uid: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск",         callback_data="menu_search")
    kb.button(text="👤 Профиль",       callback_data="menu_profile")
    kb.button(text="👨‍💻 Пожаловаться на баг",    callback_data="menu_creator")
    kb.button(text="🪞 Создать зеркало", callback_data="menu_mirror")
    if is_admin(uid):
        kb.button(text="⚙️ Админ панель", callback_data="admin_panel")
    kb.adjust(2, 2, 1) if is_admin(uid) else kb.adjust(2, 1, 1)
    return kb.as_markup()

def search_types_keyboard():
    kb = InlineKeyboardBuilder()
    for type_key, (emoji, label, _) in SEARCH_TYPES.items():
        kb.button(text=f"{emoji} {label}", callback_data=f"stype_{type_key}")
    kb.button(text="◀️ Назад", callback_data="menu_back")
    kb.adjust(2)
    return kb.as_markup()

def after_search_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Новый поиск", callback_data="menu_search")
    kb.button(text="🏠 Главная",     callback_data="menu_back_main")
    kb.adjust(2)
    return kb.as_markup()

def admin_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Рассылка",           callback_data="admin_broadcast")
    kb.button(text="🚫 Бан по ID",          callback_data="admin_ban")
    kb.button(text="✅ Разбан по ID",        callback_data="admin_unban")
    kb.button(text="🔢 Лимит запросов",     callback_data="admin_limit")
    kb.button(text="♾ Снять лимит",        callback_data="admin_unlimit")
    kb.button(text="🪞 Список зеркал",      callback_data="admin_mirrors")
    kb.button(text="◀️ Назад",              callback_data="menu_back_main")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

# ═══════════════════════════════════════════════
#  СОЗДАНИЕ РОУТЕРА ДЛЯ ЛЮБОГО БОТА (основной + зеркала)
# ═══════════════════════════════════════════════
def make_router(is_mirror: bool = False) -> Router:
    r = Router()

    # ---- /start ----
    @r.message(Command("start"))
    async def start(message: Message):
        uid = message.from_user.id
        if is_banned(uid):
            await message.answer("🚫 Вы заблокированы.")
            return
        if not await checksubi(uid):
            kb = InlineKeyboardBuilder()
            kb.button(text="🏴‍☠️ Подписаться", url="https://t.me/+O3Nsqbyb6c8zMzli")
            kb.button(text="✅ Проверить",      callback_data="checksub")
            await message.answer_photo(
                photo=banner,
                caption="🔥 Для использования бота подпишитесь на каналы\n\n@kildoxer",
                reply_markup=kb.as_markup()
            )
            return
        get_or_create_user(uid)
        await message.answer_photo(
            photo="https://i.ibb.co/RT63FqRh/IMG-7670.jpg",
            caption="<b>[🔍] KilD0xer L0okup</b>\n\nВыбери действие:",
            parse_mode="HTML",
            reply_markup=main_keyboard(uid)
        )

    # ---- checksub ----
    @r.callback_query(F.data == "checksub")
    async def checksub_cb(callback: CallbackQuery):
        uid = callback.from_user.id
        if not await checksubi(uid):
            await callback.answer("Ты ещё не подписан", show_alert=True)
            return
        await callback.answer("✅ Доступ подтверждён", show_alert=True)
        get_or_create_user(uid)
        await callback.message.edit_caption(
            caption="<b>[🔍] Kild0xer L0okUp</b>\n\nВыбери действие:",
            parse_mode="HTML",
            reply_markup=main_keyboard(uid)
        )

    # ---- Навигация ----
    @r.callback_query(F.data == "menu_back")
    async def menu_back(callback: CallbackQuery):
        await callback.message.edit_reply_markup(reply_markup=main_keyboard(callback.from_user.id))
        await callback.answer()

    @r.callback_query(F.data == "menu_back_main")
    async def menu_back_main(callback: CallbackQuery):
        await callback.answer()
        try:
            await callback.message.edit_text("Выбери действие:", reply_markup=main_keyboard(callback.from_user.id))
        except Exception:
            await callback.message.answer("Выбери действие:", reply_markup=main_keyboard(callback.from_user.id))

    @r.callback_query(F.data == "menu_search")
    async def menu_search(callback: CallbackQuery):
        await callback.message.edit_reply_markup(reply_markup=search_types_keyboard())
        await callback.answer()

    # ---- Создатель ----
    @r.callback_query(F.data == "menu_creator")
    async def menu_creator(callback: CallbackQuery):
        await callback.answer()
        await callback.message.answer(
            "[🔍] KilD0xer L0okUp\n\n👨‍💻 <b>Чтобы пожаловаться по поводу бага пишите</b>\n\<a href='https://t.me/locga'>@locga</a>",
            parse_mode="HTML", disable_web_page_preview=True
        )

    # ---- Профиль ----
    @r.callback_query(F.data == "menu_profile")
    async def menu_profile(callback: CallbackQuery):
        await callback.answer()
        uid = callback.from_user.id
        u = get_or_create_user(uid)
        first   = u["first_seen"][:16].replace("T", " ") if u["first_seen"] else "—"
        last    = u["last_request"][:16].replace("T", " ") if u["last_request"] else "—"
        last_q  = esc(u["last_query"] or "—")
        req_cnt = u["requests"]
        lim     = get_limit(uid)
        lim_str = "♾ Безлимит" if lim is None else str(lim)

        logs_text = "".join(f"\n  • {log}" for log in reversed(u["logs"][-5:]))
        text = (
            f"👤 <b>Профиль</b>\n\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📊 Запросов: <b>{req_cnt}</b>\n"
            f"🔢 Осталось: <b>{lim_str}</b>\n"
            f"🕐 Первый вход: {first}\n"
            f"🕐 Последний запрос: {last}\n"
            f"🔎 Последний поиск: <code>{last_q}</code>"
        )
        if logs_text:
            text += f"\n\n📋 <b>Последние запросы:</b>{logs_text}"
        await callback.message.answer(text, parse_mode="HTML")

    # ---- Создать зеркало ----
    @r.callback_query(F.data == "menu_mirror")
    async def menu_mirror(callback: CallbackQuery):
        await callback.answer()
        await callback.message.answer(
            "🪞 <b>Создание зеркала</b>\n\n"
            "Отправь токен нового бота в формате:\n"
            "<code>/mirror 1234567890:AAxxxxxxxxxxxxxx</code>",
            parse_mode="HTML"
        )

    @r.message(Command("mirror"))
    async def add_mirror(message: Message):
        uid = message.from_user.id
        token = message.text.replace("/mirror", "", 1).strip()
        if not token or ":" not in token:
            await message.answer("❌ Неверный формат. Пример:\n<code>/mirror TOKEN</code>", parse_mode="HTML")
            return
        # Проверяем токен
        wait = await message.answer("⏳ Проверяю токен...")
        try:
            test_bot = Bot(token)
            me = await test_bot.get_me()
            await test_bot.session.close()
        except Exception as e:
            await wait.edit_text(f"❌ Токен недействителен: {esc(str(e)[:100])}", parse_mode="HTML")
            return

        # Проверяем дубли
        existing = [m["token"] for m in DB["mirrors"]]
        if token in existing:
            await wait.edit_text("⚠️ Это зеркало уже добавлено.")
            return

        label = f"@{me.username}"
        DB["mirrors"].append({"token": token, "label": label})
        save_data(DB)

        # Запускаем зеркало
        await launch_mirror(token, label)
        await wait.edit_text(
            f"✅ Зеркало <b>{esc(label)}</b> запущено!\n"
            f"Бот: <a href='https://t.me/{me.username}'>{esc(label)}</a>",
            parse_mode="HTML"
        )

    # ---- Выбор типа поиска ----
    @r.callback_query(F.data.startswith("stype_"))
    async def select_search_type(callback: CallbackQuery):
        uid      = callback.from_user.id
        type_key = callback.data.replace("stype_", "")
        if type_key not in SEARCH_TYPES:
            await callback.answer("Неизвестный тип", show_alert=True)
            return
        user_search_type[uid] = type_key
        emoji, label, example = SEARCH_TYPES[type_key]
        await callback.answer(f"Выбрано: {label}")
        await callback.message.answer(
            f"{emoji} <b>Тип поиска: {label}</b>\n\nВведи данные:\n<i>{example}</i>",
            parse_mode="HTML"
        )

    # ---- ПОИСК ----
    @r.message(F.text & ~F.text.startswith("/"))
    async def handler(message: Message):
        uid = message.from_user.id
        if is_banned(uid):
            await message.answer("🚫 Вы заблокированы.")
            return
        if not await checksubi(uid):
            await message.answer("❌ Нужна подписка на канал")
            return
        if uid not in user_search_type:
            await message.answer(
                "⚠️ Сначала выбери тип поиска — нажми <b>🔍 Поиск</b>",
                parse_mode="HTML", reply_markup=main_keyboard(uid)
            )
            return
        if not use_request(uid):
            lim = get_limit(uid)
            await message.answer(f"❌ Лимит исчерпан. Осталось запросов: <b>{lim}</b>", parse_mode="HTML")
            return

        query       = message.text.strip()
        search_type = user_search_type[uid]
        wait        = await message.answer("⏳ Ищу...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_URL,
                    params={"key": API_KEY, "search": query},
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as resp:
                    data = await resp.json(content_type=None)
        except asyncio.TimeoutError:
            await wait.edit_text("❌ Таймаут — API не ответил за 90 сек")
            return
        except Exception as e:
            await wait.edit_text(f"❌ Ошибка соединения: {esc(str(e)[:120])}", parse_mode="HTML")
            return

        has_data = (
            data.get("success") or
            data.get("results_count", 0) > 0 or
            data.get("fast-result") or
            (data.get("full-result") or {}).get("Базы Данных")
        )
        if not has_data:
            err = data.get("error") or data.get("message") or "Ничего не найдено"
            await wait.edit_text(f"❌ {esc(err)}", parse_mode="HTML")
            return

        update_user_stat(uid, search_type, query)
        html_bytes = build_html_report(data, query, search_type).encode("utf-8")
        doc = BufferedInputFile(html_bytes, filename=f"report_{query[:20].replace(' ', '_')}.html")
        await wait.delete()
        await message.answer_document(
            document=doc,
            caption=(
                f"✅ <b>Готово!</b>\n\n"
                f"🔎 Запрос: <code>{esc(query)}</code>\n"
                f"📦 Результатов: <b>{data.get('results_count', 0)}</b>\n"
                f"📚 Источников: <b>{data.get('sources_count', 0)}</b>"
            ),
            parse_mode="HTML",
            reply_markup=after_search_keyboard()
        )

    # ════════════════════════════════════
    #  АДМИН ПАНЕЛЬ (только основной бот)
    # ════════════════════════════════════
    if not is_mirror:

        @r.callback_query(F.data == "admin_panel")
        async def admin_panel(callback: CallbackQuery):
            if not is_admin(callback.from_user.id):
                await callback.answer("⛔ Нет доступа", show_alert=True)
                return
            await callback.answer()
            mirrors_count = len(DB["mirrors"])
            users_count   = len(DB["users"])
            banned_count  = len(DB["banned"])
            await callback.message.answer(
                f"⚙️ <b>Админ панель</b>\n\n"
                f"👥 Пользователей: <b>{users_count}</b>\n"
                f"🪞 Зеркал: <b>{mirrors_count}</b>\n"
                f"🚫 Банов: <b>{banned_count}</b>",
                parse_mode="HTML",
                reply_markup=admin_keyboard()
            )

        # -- Рассылка --
        @r.callback_query(F.data == "admin_broadcast")
        async def admin_broadcast_start(callback: CallbackQuery):
            if not is_admin(callback.from_user.id): return
            await callback.answer()
            admin_state[callback.from_user.id] = "broadcast"
            await callback.message.answer("📢 Введи текст рассылки (HTML поддерживается):")

        # -- Бан --
        @r.callback_query(F.data == "admin_ban")
        async def admin_ban_start(callback: CallbackQuery):
            if not is_admin(callback.from_user.id): return
            await callback.answer()
            admin_state[callback.from_user.id] = "ban"
            await callback.message.answer("🚫 Введи ID пользователя для бана:")

        # -- Разбан --
        @r.callback_query(F.data == "admin_unban")
        async def admin_unban_start(callback: CallbackQuery):
            if not is_admin(callback.from_user.id): return
            await callback.answer()
            admin_state[callback.from_user.id] = "unban"
            await callback.message.answer("✅ Введи ID пользователя для разбана:")

        # -- Лимит --
        @r.callback_query(F.data == "admin_limit")
        async def admin_limit_start(callback: CallbackQuery):
            if not is_admin(callback.from_user.id): return
            await callback.answer()
            admin_state[callback.from_user.id] = "limit"
            await callback.message.answer("🔢 Введи: <code>ID количество</code>\nПример: <code>123456789 10</code>", parse_mode="HTML")

        # -- Снять лимит --
        @r.callback_query(F.data == "admin_unlimit")
        async def admin_unlimit_start(callback: CallbackQuery):
            if not is_admin(callback.from_user.id): return
            await callback.answer()
            admin_state[callback.from_user.id] = "unlimit"
            await callback.message.answer("♾ Введи ID пользователя для снятия лимита:")

        # -- Список зеркал --
        @r.callback_query(F.data == "admin_mirrors")
        async def admin_mirrors_list(callback: CallbackQuery):
            if not is_admin(callback.from_user.id): return
            await callback.answer()
            mirrors = DB["mirrors"]
            if not mirrors:
                await callback.message.answer("🪞 Зеркал нет.")
                return
            text = "🪞 <b>Активные зеркала:</b>\n\n"
            for i, m in enumerate(mirrors, 1):
                status = "🟢 работает" if m["token"] in mirror_tasks and not mirror_tasks[m["token"]].done() else "🔴 стоп"
                text += f"{i}. {esc(m['label'])} — {status}\n"
            await callback.message.answer(text, parse_mode="HTML")

        # -- Обработка состояний админа --
        @r.message(F.text & ~F.text.startswith("/"))
        async def admin_state_handler(message: Message):
            uid = message.from_user.id
            if uid not in admin_state:
                return  # передаём обычному хендлеру — но он уже зарегистрирован выше
            # NOTE: этот хендлер регистрируется ПЕРВЫМ для основного бота
            # поэтому при наличии admin_state перехватывает сообщение
            state = admin_state.pop(uid)
            text  = message.text.strip()

            if state == "broadcast":
                await do_broadcast(message.bot, text)
                await message.answer("✅ Рассылка отправлена.")

            elif state == "ban":
                try:
                    target = int(text)
                    if target not in DB["banned"]:
                        DB["banned"].append(target)
                        save_data(DB)
                    await message.answer(f"🚫 Пользователь <code>{target}</code> заблокирован.", parse_mode="HTML")
                except ValueError:
                    await message.answer("❌ Неверный ID")

            elif state == "unban":
                try:
                    target = int(text)
                    if target in DB["banned"]:
                        DB["banned"].remove(target)
                        save_data(DB)
                    await message.answer(f"✅ Пользователь <code>{target}</code> разблокирован.", parse_mode="HTML")
                except ValueError:
                    await message.answer("❌ Неверный ID")

            elif state == "limit":
                try:
                    parts  = text.split()
                    target = int(parts[0])
                    count  = int(parts[1])
                    DB["limits"][str(target)] = count
                    save_data(DB)
                    await message.answer(f"🔢 Пользователю <code>{target}</code> установлен лимит: <b>{count}</b>", parse_mode="HTML")
                except (ValueError, IndexError):
                    await message.answer("❌ Формат: <code>ID количество</code>", parse_mode="HTML")

            elif state == "unlimit":
                try:
                    target = int(text)
                    DB["limits"].pop(str(target), None)
                    save_data(DB)
                    await message.answer(f"♾ Лимит снят с пользователя <code>{target}</code>", parse_mode="HTML")
                except ValueError:
                    await message.answer("❌ Неверный ID")

    return r


# ═══════════════════════════════════════════════
#  РАССЫЛКА ПО ВСЕМ БОТАМ
# ═══════════════════════════════════════════════
async def do_broadcast(main_bot: Bot, text: str):
    all_uids = [int(k) for k in DB["users"].keys()]
    # Отправляем через основной бот
    for uid in all_uids:
        try:
            await main_bot.send_message(uid, text, parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.05)
    # Отправляем через зеркала
    for token, bot in mirror_bots.items():
        for uid in all_uids:
            try:
                await bot.send_message(uid, text, parse_mode="HTML")
            except Exception:
                pass
            await asyncio.sleep(0.05)

# ═══════════════════════════════════════════════
#  ЗАПУСК ЗЕРКАЛА
# ═══════════════════════════════════════════════
async def launch_mirror(token: str, label: str):
    if token in mirror_tasks and not mirror_tasks[token].done():
        return  # уже работает

    async def run():
        bot = Bot(
            token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        mirror_bots[token] = bot
        dp  = Dispatcher()
        dp.include_router(make_router(is_mirror=True))
        print(f"[MIRROR] {label} запущен")
        try:
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            print(f"[MIRROR] {label} упал: {e}")
        finally:
            mirror_bots.pop(token, None)
            print(f"[MIRROR] {label} остановлен")

    task = asyncio.create_task(run())
    mirror_tasks[token] = task

# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════
async def main():
    global _main_bot_ref

    # Основной бот
    main_bot = Bot(
    MAIN_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
    _main_bot_ref = main_bot

    main_dp = Dispatcher()
    # Сначала регистрируем роутер с admin_state_handler (он должен быть первым для текстов)
    main_router = make_router(is_mirror=False)
    main_dp.include_router(main_router)

    # Запускаем сохранённые зеркала
    for m in DB["mirrors"]:
        asyncio.create_task(launch_mirror(m["token"], m["label"]))
        await asyncio.sleep(0.3)

    print(f"[MAIN] Основной бот запущен. Зеркал: {len(DB['mirrors'])}")
    await main_dp.start_polling(main_bot)


if __name__ == "__main__":
    asyncio.run(main())
