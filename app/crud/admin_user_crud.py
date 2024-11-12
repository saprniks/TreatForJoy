from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import AdminUser


async def get_admin_user(db: AsyncSession, user_telegram_id: int):
    result = await db.execute(select(AdminUser).where(AdminUser.user_telegram_id == user_telegram_id))
    return result.scalar_one_or_none()


async def create_admin_user(db: AsyncSession, user_telegram_id: int):
    admin_user = AdminUser(user_telegram_id=user_telegram_id)
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    return admin_user
