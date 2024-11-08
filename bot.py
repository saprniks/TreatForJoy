from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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

# Создаем основную клавиатуру с двумя кнопками: "Каталог работ" и "Навигация по каналу"
start_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="Каталог работ")],
        [KeyboardButton(text="Навигация по каналу")]
    ]
)

# Создаем inline клавиатуру для "Навигация по каналу"
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
    await message.answer("Привет! Выберите один из вариантов ниже:", reply_markup=start_keyboard)

# Обработчик нажатия кнопки "Каталог работ"
@dp.message(lambda message: message.text == "Каталог работ")
async def catalog_in_progress(message: Message):
    await message.answer("Каталог в стадии разработки.")

# Обработчик нажатия кнопки "Навигация по каналу"
@dp.message(lambda message: message.text == "Навигация по каналу")
async def navigation_options(message: Message):
    await message.answer("Выберите нужный раздел:", reply_markup=navigation_keyboard)
