from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

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
