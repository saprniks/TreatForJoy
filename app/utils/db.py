import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+asyncpg://')

# Создаем асинхронный движок с отключенным кэшированием подготовленных операторов
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"statement_cache_size": 0}  # Отключаем кэширование операторов
)

#  Настраиваем sessionmaker с использованием AsyncSession
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


# Функция для получения сессии
async def get_db():
    async with SessionLocal() as session:
        yield session

# Закрытие движка при завершении
async def dispose_engine():
    await engine.dispose()
