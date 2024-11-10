from flask import Flask, request, jsonify
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv
from bot import dp  # Импорт диспетчера из bot.py
from app.models import Base  # Импорт моделей для инициализации таблиц
from app.routes.albums import albums_bp
from app.routes.items import items_bp
import os
import asyncio
from aiogram import Bot
from aiogram.types import Update

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получаем конфигурацию из окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = '/webhook'
DATABASE_URL = os.getenv('DATABASE_URL')

# Инициализация бота и базы данных
bot = Bot(token=API_TOKEN)
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


# Функция инициализации базы данных
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы базы данных успешно инициализированы.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации таблиц базы данных: {e}")


# Создание Flask-приложения
app = Flask(__name__)

# Регистрация blueprints для API
app.register_blueprint(albums_bp, url_prefix='/api/albums')
app.register_blueprint(items_bp, url_prefix='/api/items')


# Маршрут для вебхука бота
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    # Получаем обновление от Telegram
    update = Update.de_json(request.get_json(force=True), bot)
    # Обрабатываем обновление асинхронно
    asyncio.run(dp.process_update(update))
    return 'OK', 200


# Маршрут для тестирования
@app.route('/')
def index():
    return 'Приложение работает!!!', 200


# Асинхронная функция для установки вебхука
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logger.info("Вебхук успешно установлен.")


# Асинхронная функция для удаления вебхука
async def on_shutdown():
    await bot.delete_webhook()
    logger.info("Вебхук успешно удален.")


if __name__ == '__main__':
    # Инициализация базы данных перед запуском
    init_db()

    # Устанавливаем вебхук перед запуском Flask-приложения
    asyncio.run(on_startup())

    try:
        # Запускаем Flask-приложение
        app.run(host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        # Удаление вебхука при завершении работы приложения
        asyncio.run(on_shutdown())
