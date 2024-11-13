from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Photo


async def get_photos_for_item(db: AsyncSession, item_id: int):
    result = await db.execute(select(Photo).where(Photo.item_id == item_id).order_by(Photo.display_order))
    return result.scalars().all()


async def get_first_photo_for_item(db: AsyncSession, item_id: int):
    result = await db.execute(select(Photo).where(Photo.item_id == item_id).order_by(Photo.display_order).limit(1))
    return result.scalar_one_or_none()


async def add_photo(db: AsyncSession, item_id: int, url: str, description: str = None, display_order: int = 0):
    photo = Photo(item_id=item_id, url=url, description=description, display_order=display_order)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo
