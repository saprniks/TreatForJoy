from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Album


async def get_all_albums(db: AsyncSession):
    result = await db.execute(select(Album).order_by(Album.display_order))
    return result.scalars().all()


async def get_album_by_id(db: AsyncSession, album_id: int):
    result = await db.execute(select(Album).where(Album.id == album_id))
    return result.scalar_one_or_none()


async def create_album(db: AsyncSession, title: str, display_order: int = 0, notes: str = None):
    album = Album(title=title, display_order=display_order, notes=notes)
    db.add(album)
    await db.commit()
    await db.refresh(album)
    return album


async def update_album(db: AsyncSession, album_id: int, title: str = None, display_order: int = None, notes: str = None):
    album = await get_album_by_id(db, album_id)
    if album:
        if title:
            album.title = title
        if display_order is not None:
            album.display_order = display_order
        if notes:
            album.notes = notes
        await db.commit()
        await db.refresh(album)
    return album


async def delete_album(db: AsyncSession, album_id: int):
    album = await get_album_by_id(db, album_id)
    if album:
        await db.delete(album)
        await db.commit()
    return album
