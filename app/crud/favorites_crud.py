from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import favorites_table, Item
from sqlalchemy import select, delete, insert


async def get_favorites_items(db: AsyncSession, user_id: int):
    """
    Возвращает список избранных изделий для пользователя.
    """
    stmt = select(Item).join(favorites_table).where(favorites_table.c.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def is_item_in_favorites(db: AsyncSession, user_id: int, item_id: int) -> bool:
    """
    Checks if a specific item is in the user's favorites.

    :param db: AsyncSession for database operations.
    :param user_id: The ID of the user.
    :param item_id: The ID of the item to check.
    :return: True if the item is in the user's favorites, otherwise False.
    """
    stmt = select(favorites_table).where(
        (favorites_table.c.user_id == user_id) &
        (favorites_table.c.item_id == item_id)
    )
    result = await db.execute(stmt)
    return result.first() is not None


async def toggle_favorite(db: AsyncSession, user_id: int, item_id: int) -> str:
    """
    Toggles an item's presence in a user's favorites.
    If the item is already in favorites, it removes it.
    If the item is not in favorites, it adds it.

    :param db: AsyncSession for database operations.
    :param user_id: The ID of the user.
    :param item_id: The ID of the item to toggle in favorites.
    :return: A string indicating the action performed ("added" or "removed").
    """
    # Check if the item is already in favorites
    stmt_check = select(favorites_table).where(
        (favorites_table.c.user_id == user_id) &
        (favorites_table.c.item_id == item_id)
    )
    result = await db.execute(stmt_check)
    existing_favorite = result.first()

    if existing_favorite:
        # If the item is in favorites, remove it
        stmt_remove = delete(favorites_table).where(
            (favorites_table.c.user_id == user_id) &
            (favorites_table.c.item_id == item_id)
        )
        await db.execute(stmt_remove)
        await db.commit()
        return "removed"
    else:
        # If the item is not in favorites, add it
        stmt_add = insert(favorites_table).values(user_id=user_id, item_id=item_id)
        await db.execute(stmt_add)
        await db.commit()
        return "added"
