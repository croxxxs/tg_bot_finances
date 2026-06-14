from aiogram import Bot, Dispatcher, types
import os


bot = Bot(token='8987120064:AAEzimO5D5O51DgAcHBiA3BZFIrdf6YmvOU')
dp = Dispatcher()

# Общая клавиатура (reply)
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_kb.add(
    types.KeyboardButton("➕ /add_income"),
    types.KeyboardButton("➖ /add_expense"),
    types.KeyboardButton("🎯 /set_goal"),
    types.KeyboardButton("📜 /view_transactions"),
    types.KeyboardButton("📊 /statistics"),
    types.KeyboardButton("👤 /register"),
    types.KeyboardButton("🔐 /login"),
    types.KeyboardButton("❓ /help"),
)

# Inline помощь (пример)
help_text = (
    "📘 Помощь по боту — доступные команды:\n\n"
    "👋 /start — начать\n"
    "👤 /register — регистрация\n"
    "🔐 /login — вход\n"
    "➕ /add_income [сумма] [категория] — добавить доход\n"
    "➖ /add_expense [сумма] [категория] — добавить расход\n"
    "🎯 /set_goal [сумма] [описание] — поставить цель\n"
    "📜 /view_transactions [период] [категория] — просмотр транзакций\n"
    "📊 /statistics [период] — статистика (неделя/месяц)\n\n"
    "ℹ️ Пока функции находятся в разработке — используйте /help для списка команд."
)

in_dev_text = "🔧 Функция в разработке — скоро будет доступна. Спасибо за терпение! 😊"

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать! Я бот для учёта личных финансов.\n\n"
        "Нажмите кнопку или введите команду.",
        reply_markup=main_kb,
    )

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    await message.answer(help_text, reply_markup=main_kb)

# Простая универсальная вставка "в разработке" для основных команд
@dp.message_handler(commands=["register"])
async def cmd_register(message: types.Message):
    await message.answer("👤 Регистрация: " + in_dev_text, reply_markup=main_kb)

@dp.message_handler(commands=["login"])
async def cmd_login(message: types.Message):
    await message.answer("🔐 Вход: " + in_dev_text, reply_markup=main_kb)

@dp.message_handler(commands=["add_income"])
async def cmd_add_income(message: types.Message):
    await message.answer("➕ Добавление дохода: " + in_dev_text, reply_markup=main_kb)

@dp.message_handler(commands=["add_expense"])
async def cmd_add_expense(message: types.Message):
    await message.answer("➖ Добавление расхода: " + in_dev_text, reply_markup=main_kb)

@dp.message_handler(commands=["set_goal"])
async def cmd_set_goal(message: types.Message):
    await message.answer("🎯 Установка цели: " + in_dev_text, reply_markup=main_kb)

@dp.message_handler(commands=["view_transactions"])
async def cmd_view_transactions(message: types.Message):
    await message.answer("📜 Просмотр транзакций: " + in_dev_text, reply_markup=main_kb)

@dp.message_handler(commands=["statistics"])
async def cmd_statistics(message: types.Message):
    await message.answer("📊 Статистика: " + in_dev_text, reply_markup=main_kb)

# Обработка текстовых нажатий с клавиатуры (удобство для пользователей)
@dp.message_handler(lambda msg: msg.text and msg.text.startswith("➕ /add_income"))
async def text_add_income(msg: types.Message):
    await cmd_add_income(msg)

@dp.message_handler(lambda msg: msg.text and msg.text.startswith("➖ /add_expense"))
async def text_add_expense(msg: types.Message):
    await cmd_add_expense(msg)

@dp.message_handler(lambda msg: msg.text and msg.text.startswith("🎯 /set_goal"))
async def text_set_goal(msg: types.Message):
    await cmd_set_goal(msg)

@dp.message_handler(lambda msg: msg.text and msg.text.startswith("📜 /view_transactions"))
async def text_view_transactions(msg: types.Message):
    await cmd_view_transactions(msg)

@dp.message_handler(lambda msg: msg.text and msg.text.startswith("📊 /statistics"))
async def text_statistics(msg: types.Message):
    await cmd_statistics(msg)

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("❓ Неизвестная команда. Нажмите /help для списка команд.", reply_markup=main_kb)

if __name__ == "__main__":
    dp.start_polling(bot)