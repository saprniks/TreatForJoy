from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL')  # URL веб-приложения из .env

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Настройка клавиатуры
start_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="Каталог работ", web_app=WebAppInfo(url=WEB_APP_URL))],
        [KeyboardButton(text="Навигация по каналу")]
    ]
)

navigation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Знакомство, обо мне, о канале, о пряниках, состав", url="https://t.me/treat_for_joy/875")],
    [InlineKeyboardButton(text="Мёд, входящий в состав пряников", url="https://t.me/treat_for_joy/940?single")],
    [InlineKeyboardButton(text="Палитра натуральных красителей на бумаге", url="https://t.me/treat_for_joy/1069")],
    [InlineKeyboardButton(text="Процесс окрашивания глазури", url="https://t.me/treat_for_joy/569")],
    [InlineKeyboardButton(text="Как размягчить затвердевший пряник", url="https://t.me/treat_for_joy/959")],
    [InlineKeyboardButton(text="Набор натуральных красителей", url="https://t.me/treat_for_joy/1484")]
])

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    logger.info("Received /start command from user: %s", message.from_user.id)
    await message.answer("Привет! Выберите один из вариантов ниже:", reply_markup=start_keyboard)

# Обработчик кнопки "Навигация по каналу"
@dp.message(lambda message: message.text == "Навигация по каналу")
async def navigation_options(message: Message):
    logger.info("User %s requested 'Навигация по каналу'", message.from_user.id)
    await message.answer("Выберите нужный раздел:", reply_markup=navigation_keyboard)
