from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Item


async def get_all_items(db: AsyncSession):
    result = await db.execute(select(Item).order_by(Item.display_order))
    return result.scalars().all()


async def get_item_by_id(db: AsyncSession, item_id: int):
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


async def create_item(db: AsyncSession, title: str, description: str = None, sku: str = None, price: float = 0.0):
    item = Item(title=title, description=description, sku=sku, price=price)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item(db: AsyncSession, item_id: int, title: str = None, description: str = None, price: float = None):
    item = await get_item_by_id(db, item_id)
    if item:
        if title:
            item.title = title
        if description:
            item.description = description
        if price is not None:
            item.price = price
        await db.commit()
        await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: int):
    item = await get_item_by_id(db, item_id)
    if item:
        await db.delete(item)
        await db.commit()
    return item
