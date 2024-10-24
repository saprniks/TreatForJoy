from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я фото бот.")


# Основная асинхронная функция для запуска бота
async def main():
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запуск асинхронного приложения
    asyncio.run(main())
