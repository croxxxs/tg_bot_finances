import os
import asyncio
from datetime import datetime, timedelta
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import F

DB_PATH = os.getenv("DB_PATH", "finance.db")
API_TOKEN = os.getenv("TG_BOT_TOKEN",'8987120064:AAE0jozEDqkauZIXt0ziX4ZXfu-tgYpaCfQ')  # обязательно задать

if not API_TOKEN:
    raise SystemExit("Set TG_BOT_TOKEN environment variable")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Keyboard
kb = ReplyKeyboardBuilder()
kb.row(
    types.KeyboardButton(text="➕ /add_income"),
    types.KeyboardButton(text="➖ /add_expense"),
)
kb.row(
    types.KeyboardButton(text="🎯 /set_goal"),
    types.KeyboardButton(text="📜 /view_transactions"),
)
kb.row(
    types.KeyboardButton(text="📊 /statistics"),
    types.KeyboardButton(text="👤 /register"),
)
kb.row(
    types.KeyboardButton(text="🔐 /login"),
    types.KeyboardButton(text="❓ /help"),
)
MAIN_KB = kb.as_markup(resize_keyboard=True)

HELP_TEXT = (
    "📘 Команды:\n"
    "/start — старт\n"
    "/register — регистрация\n"
    "/add_income [сумма] [категория]\n"
    "/add_expense [сумма] [категория]\n"
    "/set_goal [сумма] [описание]\n"
    "/view_transactions [период] [категория]\n"
    "  периоды: день/неделя/месяц/год\n"
    "/statistics [период]\n"
)

# Database helpers
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            created_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            type TEXT, -- income/expense
            amount REAL,
            category TEXT,
            description TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            target REAL,
            description TEXT,
            created_at TEXT,
            notified INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        await db.commit()

async def get_user_row_by_telegram(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        await cur.close()
        return row

async def ensure_user(telegram_id: int, username: str | None):
    row = await get_user_row_by_telegram(telegram_id)
    if row:
        return row["id"]
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO users (telegram_id, username, created_at) VALUES (?, ?, ?)",
            (telegram_id, username, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid

# Util: parse amount
def parse_amount(s: str):
    try:
        a = float(s.replace(",", "."))
        if a <= 0:
            return None
        return round(a, 2)
    except:
        return None

# Period helpers
def period_start(period: str):
    now = datetime.utcnow()
    p = period.lower() if period else "month"
    if p in ("день", "day"):
        return now - timedelta(days=1)
    if p in ("неделя", "week"):
        return now - timedelta(weeks=1)
    if p in ("месяц", "month"):
        return now - timedelta(days=30)
    if p in ("год", "year"):
        return now - timedelta(days=365)
    # default month
    return now - timedelta(days=30)

# Handlers
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для учёта финансов.\nНажми /register чтобы начать.",
        reply_markup=MAIN_KB,
    )

@dp.message(Command(commands=["help"]))
async def cmd_help(message: types.Message):
    await message.answer(HELP_TEXT, reply_markup=MAIN_KB)

@dp.message(Command(commands=["register"]))
async def cmd_register(message: types.Message):
    user = message.from_user
    uid = await ensure_user(user.id, user.username)
    await message.answer(f"👤 Вы зарегистрированы (id={uid}).", reply_markup=MAIN_KB)

@dp.message(Command(commands=["login"]))
async def cmd_login(message: types.Message):
    row = await get_user_row_by_telegram(message.from_user.id)
    if row:
        await message.answer("🔐 Вы вошли.", reply_markup=MAIN_KB)
    else:
        await message.answer("⚠️ Вы не зарегистрированы. Используйте /register.", reply_markup=MAIN_KB)

@dp.message(Command(commands=["add_income"]))
async def cmd_add_income(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Использование: /add_income [сумма] [категория]\nПример: /add_income 50000 зарплата", reply_markup=MAIN_KB)
        return
    amount = parse_amount(parts[1])
    if amount is None:
        await message.answer("Неверная сумма. Введите число > 0.", reply_markup=MAIN_KB)
        return
    category = parts[2].strip() if len(parts) == 3 else "прочее"
    user_row = await get_user_row_by_telegram(message.from_user.id)
    if not user_row:
        await message.answer("⚠️ Сначала зарегистрируйтесь: /register", reply_markup=MAIN_KB)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, type, amount, category, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (user_row["id"], "income", amount, category, "", datetime.utcnow().isoformat()),
        )
        await db.commit()
    await message.answer(f"✅ Доход {amount} записан в категорию '{category}'.", reply_markup=MAIN_KB)
    await check_goals(user_row["id"], message)

@dp.message(Command(commands=["add_expense"]))
async def cmd_add_expense(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Использование: /add_expense [сумма] [категория]\nПример: /add_expense 1200 еда", reply_markup=MAIN_KB)
        return
    amount = parse_amount(parts[1])
    if amount is None:
        await message.answer("Неверная сумма. Введите число > 0.", reply_markup=MAIN_KB)
        return
    category = parts[2].strip() if len(parts) == 3 else "прочее"
    user_row = await get_user_row_by_telegram(message.from_user.id)
    if not user_row:
        await message.answer("⚠️ Сначала зарегистрируйтесь: /register", reply_markup=MAIN_KB)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, type, amount, category, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (user_row["id"], "expense", amount, category, "", datetime.utcnow().isoformat()),
        )
        await db.commit()
    await message.answer(f"✅ Расход {amount} записан в категорию '{category}'.", reply_markup=MAIN_KB)

@dp.message(Command(commands=["set_goal"]))
async def cmd_set_goal(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Использование: /set_goal [сумма] [описание]\nПример: /set_goal 100000 отпуск", reply_markup=MAIN_KB)
        return
    target = parse_amount(parts[1])
    if target is None:
        await message.answer("Неверная сумма цели.", reply_markup=MAIN_KB)
        return
    desc = parts[2].strip() if len(parts) == 3 else ""
    user_row = await get_user_row_by_telegram(message.from_user.id)
    if not user_row:
        await message.answer("⚠️ Сначала зарегистрируйтесь: /register", reply_markup=MAIN_KB)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO goals (user_id, target, description, created_at) VALUES (?, ?, ?, ?)",
            (user_row["id"], target, desc, datetime.utcnow().isoformat()),
        )
        await db.commit()
    await message.answer(f"🎯 Цель установлена: {target} — {desc}", reply_markup=MAIN_KB)
    await check_goals(user_row["id"], message)

async def check_goals(user_id: int, message: types.Message):
    # вычислить накопленную сумму (net income - expenses) или только доходы? предположим суммарный баланс
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) as balance FROM transactions WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        balance = row["balance"] or 0.0
        cur = await db.execute("SELECT * FROM goals WHERE user_id = ? AND notified = 0", (user_id,))
        goals = await cur.fetchall()
        for g in goals:
            if balance >= g["target"]:
                await message.answer(f"🎉 Цель '{g['description']}' достигнута! Цель: {g['target']}, баланс: {balance}")
                await db.execute("UPDATE goals SET notified = 1 WHERE id = ?", (g["id"],))
        await db.commit()

@dp.message(Command(commands=["view_transactions"]))
async def cmd_view_transactions(message: types.Message):
    parts = message.text.split(maxsplit=2)
    period = parts[1] if len(parts) >= 2 else "месяц"
    category = parts[2].strip() if len(parts) == 3 else None
    start = period_start(period)
    user_row = await get_user_row_by_telegram(message.from_user.id)
    if not user_row:
        await message.answer("⚠️ Сначала зарегистрируйтесь: /register", reply_markup=MAIN_KB)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM transactions WHERE user_id = ? AND timestamp >= ?"
        params = [user_row["id"], start.isoformat()]
        if category:
            q += " AND category = ?"
            params.append(category)
        q += " ORDER BY timestamp DESC LIMIT 100"
        cur = await db.execute(q, params)
        rows = await cur.fetchall()
        if not rows:
            await message.answer("Сделок не найдено за период.", reply_markup=MAIN_KB)
            return
        lines = []
        income = 0.0
        expense = 0.0
        for r in rows:
            ts = r["timestamp"][:19].replace("T", " ")
            lines.append(f"{ts} | {r['type']} | {r['amount']} | {r['category']}")
            if r["type"] == "income":
                income += r["amount"]
            else:
                expense += r["amount"]
        balance = income - expense
        text = "📜 Транзакции:\n" + "\n".join(lines[:20])
        text += f"\n\nИтого: доход {income:.2f}, расход {expense:.2f}, баланс {balance:.2f}"
        await message.answer(text, reply_markup=MAIN_KB)

@dp.message(Command(commands=["statistics"]))
async def cmd_statistics(message: types.Message):
    parts = message.text.split(maxsplit=1)
    period = parts[1] if len(parts) == 2 else "месяц"
    start = period_start(period)
    user_row = await get_user_row_by_telegram(message.from_user.id)
    if not user_row:
        await message.answer("⚠️ Сначала зарегистрируйтесь: /register", reply_markup=MAIN_KB)
        return
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT type, SUM(amount) as s FROM transactions WHERE user_id = ? AND timestamp >= ? GROUP BY type",
            (user_row["id"], start.isoformat()),
        )
        rows = await cur.fetchall()
        income = 0.0
        expense = 0.0
        for r in rows:
            if r["type"] == "income":
                income = r["s"] or 0.0
            else:
                expense = r["s"] or 0.0
        # by category (expenses)
        cur = await db.execute(
            "SELECT category, SUM(amount) as s FROM transactions WHERE user_id = ? AND timestamp >= ? GROUP BY category",
            (user_row["id"], start.isoformat()),
        )
        cats = await cur.fetchall()
        total = sum((c["s"] or 0.0) for c in cats)
        lines = []
        for c in cats:
            pct = (c["s"] / total * 100) if total > 0 else 0
            lines.append(f"{c['category']}: {c['s']:.2f} ({pct:.1f}%)")
        text = f"📊 Статистика ({period}):\nДоход: {income:.2f}\nРасход: {expense:.2f}\nБаланс: {income - expense:.2f}\n\nКатегории:\n" + ("\n".join(lines) if lines else "нет данных")
        await message.answer(text, reply_markup=MAIN_KB)

# Fallback for keyboard presses
@dp.message(F.text == "➕ /add_income")
async def kb_add_income(msg: types.Message):
    await cmd_add_income(msg)

@dp.message(F.text == "➖ /add_expense")
async def kb_add_expense(msg: types.Message):
    await cmd_add_expense(msg)

@dp.message(F.text == "🎯 /set_goal")
async def kb_set_goal(msg: types.Message):
    await cmd_set_goal(msg)

@dp.message(F.text == "📜 /view_transactions")
async def kb_view_transactions(msg: types.Message):
    await cmd_view_transactions(msg)

@dp.message(F.text == "📊 /statistics")
async def kb_statistics(msg: types.Message):
    await cmd_statistics(msg)

@dp.message()
async def fallback(message: types.Message):
    await message.answer("❓ Неизвестная команда. Используйте /help.", reply_markup=MAIN_KB)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())