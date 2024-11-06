from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import asyncio
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL, куда Telegram будет отправлять обновления

if not API_TOKEN or not WEBHOOK_URL:
    logger.error("Отсутствует TELEGRAM_BOT_TOKEN или WEBHOOK_URL в переменных окружения.")
else:
    logger.info("Переменные окружения успешно загружены.")

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
    logger.info(f"Пользователь {message.from_user.id} использовал команду /start")
    await message.answer("Привет! Нажми на кнопку ниже, чтобы начать работу с ботом.", reply_markup=start_keyboard)

# Обработчик нажатия кнопки "Старт"
@dp.message(lambda message: message.text == "🚀 Старт")
async def start_bot(message: Message):
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Старт'")
    await message.answer("Бот запущен! Чем могу помочь?")

# Основная асинхронная функция для установки вебхука
async def on_startup(app: web.Application):
    logger.info("Запуск приложения и установка вебхука...")
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info("Вебхук успешно установлен.")
    except Exception as e:
        logger.error(f"Ошибка установки вебхука: {e}")

async def on_shutdown(app: web.Application):
    logger.info("Остановка приложения и удаление вебхука...")
    try:
        await bot.delete_webhook()
        logger.info("Вебхук успешно удален.")
    except Exception as e:
        logger.error(f"Ошибка удаления вебхука: {e}")

# Настройка веб-сервера для приема обновлений
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

if __name__ == "__main__":
    logger.info("Запуск веб-сервера...")
    # Запуск веб-сервера
    web.run_app(app, port=8000)
