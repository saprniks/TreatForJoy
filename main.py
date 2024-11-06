from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, Update
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

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я фото бот.")

# Основная асинхронная функция для запуска бота через вебхук
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
