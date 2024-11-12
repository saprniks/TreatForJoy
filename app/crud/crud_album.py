from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Album

async def get_albums(db: AsyncSession):
    """Получить список всех альбомов."""
    result = await db.execute(select(Album).order_by(Album.display_order))
    return result.scalars().all()

async def get_album(db: AsyncSession, album_id: int):
    """Получить альбом по ID."""
    result = await db.execute(select(Album).filter(Album.id == album_id))
    return result.scalars().first()

async def create_album(db: AsyncSession, title: str, display_order: int = 0, notes: str = None):
    """Создать новый альбом."""
    new_album = Album(title=title, display_order=display_order, notes=notes)
    db.add(new_album)
    await db.commit()
    await db.refresh(new_album)
    return new_album

async def delete_album(db: AsyncSession, album_id: int):
    """Удалить альбом по ID."""
    album = await get_album(db, album_id)
    if album:
        await db.delete(album)
        await db.commit()
    return album
