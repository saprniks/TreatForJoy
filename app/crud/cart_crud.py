from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, update
from app.models.models import Cart
from datetime import datetime


async def get_cart_items_for_user(db: AsyncSession, user_id: int):
    """
    Получение всех товаров в корзине пользователя.
    """
    stmt = select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.item))
    result = await db.execute(stmt)
    return result.scalars().all()


async def add_or_update_cart_item(db: AsyncSession, user_id: int, item_id: int, quantity: int = 1):
    """
    Добавление нового товара в корзину или обновление количества, если товар уже в корзине.
    """
    # Проверяем, есть ли уже товар в корзине
    stmt = select(Cart).where(
        (Cart.user_id == user_id) & (Cart.item_id == item_id) & (Cart.checkout_timestamp == None)
    )
    result = await db.execute(stmt)
    cart_item = result.scalar()

    if cart_item:
        # Увеличиваем количество, если запись существует
        cart_item.quantity += quantity
    else:
        # Создаем новую запись
        cart_item = Cart(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            created_at=datetime.utcnow()
        )

    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)
    return cart_item


async def get_quantity(db: AsyncSession, user_id: int, item_id: int):
    stmt = select(Cart.quantity).where(
        (Cart.user_id == user_id) &
        (Cart.item_id == item_id) &
        (Cart.checkout_timestamp == None)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def update_quantity(db: AsyncSession, user_id: int, item_id: int, action: str):
    stmt = select(Cart).where(
        (Cart.user_id == user_id) &
        (Cart.item_id == item_id) &
        (Cart.checkout_timestamp == None)
    )
    result = await db.execute(stmt)
    cart_item = result.scalar()

    if action == "increase":
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = Cart(user_id=user_id, item_id=item_id, quantity=1)
            db.add(cart_item)
    elif action == "decrease" and cart_item:
        cart_item.quantity = max(0, cart_item.quantity - 1)

    await db.commit()
    await db.refresh(cart_item)
    return cart_item.quantity if cart_item else 0


async def delete_cart_item(db: AsyncSession, user_id: int, item_id: int):
    stmt = delete(Cart).where(
        (Cart.user_id == user_id) &
        (Cart.item_id == item_id) &
        (Cart.checkout_timestamp == None)
    )
    await db.execute(stmt)
    await db.commit()
