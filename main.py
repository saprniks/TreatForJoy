from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL, куда Telegram будет отправлять обновления

# Инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем клавиатуру с кнопкой "Старт"
start_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="🚀 Старт")]
    ]
)

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Нажми на кнопку ниже, чтобы начать работу с ботом.", reply_markup=start_keyboard)

# Обработчик нажатия кнопки "Старт"
@dp.message(lambda message: message.text == "🚀 Старт")
async def start_bot(message: Message):
    await message.answer("Бот запущен! Чем могу помочь?")

# Основная асинхронная функция для установки вебхука
async def on_startup(app: web.Application):
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    # Убираем вебхук при завершении работы
    await bot.delete_webhook()

# Настройка веб-сервера для приема обновлений
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

if __name__ == "__main__":
    # Запуск веб-сервера
    web.run_app(app, port=8000)
