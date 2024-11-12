from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Cart


async def get_cart_items_for_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    return result.scalars().all()


async def add_item_to_cart(db: AsyncSession, user_id: int, item_id: int, quantity: int = 1):
    cart_item = Cart(user_id=user_id, item_id=item_id, quantity=quantity)
    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)
    return cart_item
