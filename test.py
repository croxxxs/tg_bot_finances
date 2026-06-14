import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command
from aiogram import asyncio



bot = Bot(token='8987120064:AAEzimO5D5O51DgAcHBiA3BZFIrdf6YmvOU')
dp = Dispatcher()

# Построение reply-клавиатуры (aiogram v3)
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
main_kb = kb.as_markup(resize_keyboard=True)

help_text = "📘 Помощь...\n(команды перечислены)"

in_dev_text = "🔧 Функция в разработке — скоро будет доступна. 😊"

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer("👋 Добро пожаловать!", reply_markup=main_kb)

@dp.message(Command(commands=["help"]))
async def cmd_help(message: types.Message):
    await message.answer(help_text, reply_markup=main_kb)

@dp.message(Command(commands=["add_income"]))
async def cmd_add_income(message: types.Message):
    await message.answer("➕ " + in_dev_text, reply_markup=main_kb)

# остальные handlers аналогично...

@dp.message()
async def fallback(message: types.Message):
    await message.answer("❓ Неизвестная команда. Нажмите /help.", reply_markup=main_kb)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))