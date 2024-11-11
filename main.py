import logging
import os
import requests
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models import Base
from app.utils.db import get_db  # функция для получения сессии БД
from bot import bot, dp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Dispatcher
from aiogram.types import Update

# Загрузка переменных окружения из .env
load_dotenv()

# Настройки
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+asyncpg://')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 8000))

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройка FastAPI приложения
app = FastAPI()

# Настройка базы данных
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Инициализация базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

# Функция проверки состояния вебхука
def check_webhook_status():
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info["ok"]:
                logger.info("Webhook info retrieved successfully: %s", webhook_info["result"])
            else:
                logger.warning("Failed to retrieve webhook info: %s", webhook_info)
        else:
            logger.error("Error fetching webhook info, HTTP status code: %s", response.status_code)
    except Exception as e:
        logger.error("Exception occurred while fetching webhook info: %s", e)

# Настройка вебхука при запуске приложения
@app.on_event("startup")
async def on_startup():
    logger.info("Setting webhook...")
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logger.info("Webhook set successfully!")
    await init_db()

    # Планировщик для периодической проверки вебхука
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_webhook_status, "interval", minutes=7)
    scheduler.start()
    logger.info("Scheduler started for periodic webhook checks.")

# Удаление вебхука при завершении работы приложения
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Deleting webhook...")
    await bot.delete_webhook()
    await engine.dispose()

# Эндпоинт для получения обновлений от Telegram
@app.post(WEBHOOK_PATH)
async def telegram_webhook(update: dict):
    telegram_update = Update.to_object(update)
    await dp.process_update(telegram_update)
    return {"ok": True}

# Маршрут для проверки состояния приложения
@app.get("/")
async def read_root():
    return {"message": "Telegram bot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
