from aiohttp import web
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from bot import bot, dp  # Импортируем бота и диспетчер из bot.py
from app.models import Base  # Импортируем Base из models для инициализации таблиц
import os
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env
load_dotenv()

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

# Настройка базы данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для тестирования подключения к базе данных
def test_db_connection():
    try:
        connection = engine.connect()
        logger.info("Успешное подключение к базе данных.")
        connection.close()
    except Exception as e:
        logger.error("Ошибка при подключении к базе данных: %s", e)

# Функция для инициализации таблиц
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы успешно инициализированы.")
    except Exception as e:
        logger.error("Ошибка при инициализации таблиц: %s", e)

# Асинхронная функция для установки вебхука и инициализации базы данных
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Вебхук успешно установлен.")

    logger.info("Проверка подключения к базе данных...")
    test_db_connection()
    logger.info("Инициализация таблиц базы данных...")
    init_db()

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
