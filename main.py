from aiohttp import web
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from bot import bot, dp
from app.models import Base
import os
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
DATABASE_URL = os.getenv('DATABASE_URL')
WEBHOOK_PATH = "/webhook"
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to test database connection
def test_db_connection():
    try:
        connection = engine.connect()
        logger.info("Database connection successful.")
        connection.close()
    except Exception as e:
        logger.error("Database connection error: %s", e)

# Function to initialize tables
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error("Error initializing tables: %s", e)

# Function to check and log webhook status
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

# Async function to set webhook, initialize database, and start scheduler
async def on_startup(app: web.Application):
    logger.info("Attempting to set webhook with URL: %s", WEBHOOK_URL + WEBHOOK_PATH)
    try:
        await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
        logger.info("Webhook set successfully!")
    except Exception as e:
        logger.error("Failed to set webhook: %s", e)

    # Check webhook status after setting it
    check_webhook_status()

    logger.info("Checking database connection...")
    test_db_connection()
    logger.info("Initializing database tables...")
    init_db()

    # Start scheduler for periodic webhook checks
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_webhook_status, "interval", minutes=1)
    scheduler.start()
    logger.info("Scheduler started for periodic webhook checks every 1 minute.")

async def on_shutdown(app: web.Application):
    logger.info("Deleting webhook...")
    try:
        await bot.delete_webhook()
        logger.info("Webhook deleted successfully.")
    except Exception as e:
        logger.error("Failed to delete webhook: %s", e)

# Configure web server to handle updates
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)

if __name__ == "__main__":
    logger.info("Starting web server...")
    # Run the web server
    web.run_app(app, port=8000)
