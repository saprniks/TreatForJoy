from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import os
import logging
import psycopg2  # Импорт библиотеки для работы с PostgreSQL
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

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


# Функция для тестирования подключения к базе данных
def test_db_connection():
    try:
        # Подключаемся к базе данных
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # Выполняем простой запрос
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        # Логируем результат запроса
        if result:
            logger.info("Успешное подключение к базе данных. Результат тестового запроса: %s", result)
        else:
            logger.warning("Тестовый запрос вернул пустой результат.")

        # Закрываем соединение
        cursor.close()
        connection.close()
    except Exception as e:
        logger.error("Ошибка при подключении к базе данных: %s", e)


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Нажми на кнопку ниже, чтобы начать работу с ботом.", reply_markup=start_keyboard)


# Обработчик нажатия кнопки "Старт"
@dp.message(lambda message: message.text == "🚀 Старт")
async def start_bot(message: Message):
    await message.answer("Бот запущен! Чем могу помочь?")


# Основная асинхронная функция для установки вебхука и проверки базы данных
async def on_startup(app: web.Application):
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Вебхук успешно установлен.")

    # Проверка подключения к базе данных
    logger.info("Проверка подключения к базе данных...")
    test_db_connection()


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("Вебхук успешно удален.")


# Настройка веб-сервера для приема обновлений
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

if __name__ == "__main__":
    # Запуск веб-сервера
    web.run_app(app, port=8000)
