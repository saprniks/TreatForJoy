# user_crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import User


async def get_user_by_telegram_id(db: AsyncSession, user_telegram_id: int):
    result = await db.execute(select(User).where(User.user_telegram_id == user_telegram_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, full_name: str, username: str, user_telegram_id: int, avatar_url: str = None):
    user = User(full_name=full_name, username=username, user_telegram_id=user_telegram_id, avatar_url=avatar_url)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def add_user_if_not_exists(session: AsyncSession, user_data: dict):
    # Извлекаем user_telegram_id из данных
    user_telegram_id_from_web = user_data.get("id")
    print("User data received:", user_data)  # Отладочный вывод

    # Проверяем, существует ли пользователь с таким user_telegram_id
    result = await session.execute(select(User).where(User.user_telegram_id == user_telegram_id_from_web))
    existing_user = result.scalars().first()

    if existing_user is None:
        print("User not found, creating new user")  # Отладочный вывод
        # Если пользователь не найден, создаем новую запись
        new_user = User(
            user_telegram_id=user_telegram_id_from_web,
            full_name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
            username=user_data.get("username"),
            avatar_url=user_data.get("photo_url")
        )
        session.add(new_user)
        await session.commit()
        print("User created successfully:", new_user)
    else:
        print("User already exists, skipping creation")  # Отладочный вывод
