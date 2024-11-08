# utils/db.py
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

# Загружаем переменные окружения
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Настройка базы данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session() -> Session:
    """
    Получение сессии для работы с базой данных.
    Используется в качестве контекстного менеджера для автоматического закрытия сессии.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
