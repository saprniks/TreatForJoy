from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud import album_crud, user_crud, item_crud, photo_crud, favorites_crud, cart_crud, admin_user_crud
from app.utils.db import get_db
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import urllib.parse
import os
from dotenv import load_dotenv


load_dotenv()  # Загружаем переменные из .env
WEB_APP_URL = os.getenv("WEB_APP_URL")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def init_reg_page():
    """
    Рендеринг начальной страницы с JavaScript.
    """
    logger.info("Rendering init_reg.html")
    return templates.TemplateResponse("init_reg.html", {"request": {}, "web_app_url": WEB_APP_URL})


@router.post("/register")
async def get_tg_user_id(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Обработка данных пользователя и перенаправление на следующую страницу.
    """
    data = await request.json()
    tg_user_id = data.get("id", "Неизвестный пользователь")  # Извлекаем tg_user_id из данных

    # Логирование
    logger.info(f"Extracted user_id: {tg_user_id}")
    logger.info(f"Extracted data: {data}")
#   Вызываем функцию для проверки и добавления пользователя, если он не существует
    await user_crud.add_user_if_not_exists(db, data)

    # Возвращаем URL для следующей страницы
    return {"next_page_url": f"{WEB_APP_URL}/index?tg_user_id={tg_user_id}"}


@router.get("/index", response_class=HTMLResponse)
async def index_page(tg_user_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Рендеринг страницы с user_id.
    """
    user = await user_crud.get_user_by_telegram_id(db, int(tg_user_id))
    user_id = user.id
    logger.info(f"Rendering index.html for user_id: {tg_user_id}")

    # Запрашиваем все альбомы и изделия из базы данных
    albums = await album_crud.get_all_albums(db)
    items_all = await item_crud.get_all_items(db)

    # Фильтруем альбомы и изделия, у которых is_visible = False
    visible_albums = [album for album in albums if album.is_visible]
    visible_items = [item for item in items_all if item.is_visible]

    # Отбираем первые три изделия по display_order для каждого альбома
    filtered_items = []
    for album in visible_albums:
        album_items = [item for item in visible_items if item.album_id == album.id]
        album_items = sorted(album_items, key=lambda item: item.display_order)[:3]
        filtered_items.extend(album_items)

    # Сортируем итоговый список изделий по display_order в возрастающем порядке
    filtered_items = sorted(filtered_items, key=lambda item: item.display_order)

    # Добавляем к каждой item поле photo с display_order = 1
    for item in filtered_items:
        photo = await photo_crud.get_first_photo_for_item(db, item.id)
        if photo:
            item.photo_url = photo.url
        else:
            item.photo_url = "https://skcdwguqcbkqxsqrgswd.supabase.co/storage/v1/object/public/misc//no-image-large.jpg"

    # Получаем корзину пользователя
    cart_items = await cart_crud.get_cart_items_for_user(db, user_id)

    # Создаем словарь {item_id: {"quantity": quantity}}
    cart_data = {cart_item.item.id: {"quantity": cart_item.quantity} for cart_item in cart_items}

    # Проверяем, админ ли пользователь
    current_user_tg_id = await user_crud.get_user_tg_id_by_user_id(db, user_id)
    is_admin = await admin_user_crud.is_current_user_admin(db, current_user_tg_id)

    # рендерим страницу
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "albums": visible_albums,  # Передаем только видимые альбомы
            "items": filtered_items,  # Передаем только отфильтрованные изделия
            "user_id": user_id,
            "cart_items": cart_data,  # Передаем данные корзины
            "is_admin": is_admin,
        }
    )
    # Добавляем заголовки, запрещающие кеширование
    response.headers["Cache-Control"] = "no-store"
    return response




@router.get("/favorites", response_class=HTMLResponse)
async def view_favorites(
    user_id: int,  # Получаем user_id из параметров URL
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Страница избранного для текущего пользователя.
    """
    # Получаем все избранные изделия пользователя
    favorite_items = await favorites_crud.get_favorites_items(db, user_id)

    # Фильтруем альбомы и изделия, у которых is_visible = False
    favorite_items = [item for item in favorite_items if item.is_visible]

    # Добавляем URL первой фотографии для каждого изделия
    for item in favorite_items:
        photo = await photo_crud.get_first_photo_for_item(db, item.id)
        item.photo_url = photo.url

    # Получаем корзину пользователя
    cart_items = await cart_crud.get_cart_items_for_user(db, user_id)

    # Создаем словарь {item_id: {"quantity": quantity}}
    cart_data = {cart_item.item.id: {"quantity": cart_item.quantity} for cart_item in cart_items}


    # Логируем процесс и рендерим страницу
    logger.info(f"Rendering favorites.html for user_id: {user_id}")
    response = templates.TemplateResponse(
        "favorites.html", {"request": request, "items": favorite_items, "user_id": user_id, "cart_items": cart_data}
    )
    # Добавляем заголовки, запрещающие кеширование
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/album/{album_id}", response_class=HTMLResponse)
async def view_album(
    album_id: int,
    user_id: int,  # Add user_id as a query parameter
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Retrieve the album and its items by album_id
    album = await album_crud.get_album_by_id(db, album_id)
    items = await item_crud.get_items_by_album_id(db, album_id)

    # Фильтруем альбомы и изделия, у которых is_visible = False
    items = [item for item in items if item.is_visible]


    # Add a photo with display_order = 1 to each item
    for item in items:
        photo = await photo_crud.get_first_photo_for_item(db, item.id)
        item.photo_url = photo.url

    # Получаем корзину пользователя
    cart_items = await cart_crud.get_cart_items_for_user(db, user_id)

    # Создаем словарь {item_id: {"quantity": quantity}}
    cart_data = {cart_item.item.id: {"quantity": cart_item.quantity} for cart_item in cart_items}

    response = templates.TemplateResponse(
        "album.html", {"request": request, "album": album, "items": items, "user_id": user_id, "cart_items": cart_data}
    )

    # Добавляем заголовки, запрещающие кеширование
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/item/{item_id}", response_class=HTMLResponse)
async def view_item(item_id: int, user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # Retrieve the item and its photos by item_id
    item = await item_crud.get_item_by_id(db, item_id)
    photos = await photo_crud.get_photos_for_item(db, item_id)

    # Check if the item is in the user's favorites
    is_fav = await favorites_crud.is_item_in_favorites(db, user_id, item_id)

    # Retrieve the album title
    album = await album_crud.get_album_by_id(db, item.album_id)

    # Retrieve user information
    user = await user_crud.get_user_by_id(db, user_id)

    # Render item.html with the photos, item data, and user information
    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item": item,
            "photos": photos,
            "is_fav": is_fav,
            "user_id": user_id,
            "album": album,  # Передаем название альбома
            "user": user,    # Добавляем информацию о пользователе
        },
    )


@router.post("/api/favorites/toggle")
async def toggle_favorite(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    user_id = data.get("user_id")
    item_id = data.get("item_id")

    if not user_id or not item_id:
        return {"error": "Invalid input"}, 400

    # Call the toggle function from CRUD
    action = await favorites_crud.toggle_favorite(db, user_id, item_id)

    # Determine the new state
    is_fav = action == "added"

    return {"is_fav": is_fav}


@router.get("/cart", response_class=HTMLResponse)
async def view_cart(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Страница корзины для пользователя.
    """
    # Получаем все товары в корзине пользователя
    cart_items = await cart_crud.get_cart_items_for_user(db, user_id)

    # Добавляем URL первой фотографии для каждого изделия
    for cart_item in cart_items:
        photo = await photo_crud.get_first_photo_for_item(db, cart_item.item.id)
        cart_item.item.photo_url = photo.url

    # Рассчитываем общую сумму
    total_price = sum(cart_item.item.price * cart_item.quantity for cart_item in cart_items)

    # Sort list of cart items by their item.id in ascending order
    cart_items.sort(key=lambda x: x.item.id)

    # Добавляем заголовки, запрещающие кеширование
    response = templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "cart_items": cart_items,
            "total_price": total_price,
            "user_id": user_id,
        }
    )
    response.headers["Cache-Control"] = "no-store"
    # Рендерим страницу корзины
    return response


@router.get("/previous_orders", response_class=HTMLResponse)
async def view_orders_history(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Страница истории заказов для пользователя.
    """
    # Получаем все товары в корзине пользователя из завершенных заказов
    cart_items = await cart_crud.get_all_previous_orders(db, user_id)

    # Добавляем URL первой фотографии для каждого изделия
    for cart_item in cart_items:
        photo = await photo_crud.get_first_photo_for_item(db, cart_item.item.id)
        cart_item.item.photo_url = photo.url

    # Sort list of cart items by their item.id in ascending order
    cart_items.sort(key=lambda x: x.item.id)

    # Добавляем заголовки, запрещающие кеширование
    response = templates.TemplateResponse(
        "previous_orders.html",
        {
            "request": request,
            "cart_items": cart_items,
            "user_id": user_id,
        }
    )
    response.headers["Cache-Control"] = "no-store"
    # Рендерим страницу корзины
    return response



@router.post("/api/cart/update")
async def update_cart(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление корзины для пользователя.
    """
    data = await request.json()
    user_id = data.get("user_id")
    item_id = data.get("item_id")

    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Invalid input")

    # Вызываем CRUD функцию
    cart_item = await cart_crud.add_or_update_cart_item(db, user_id, item_id)

    return {"status": "success", "quantity": cart_item.quantity}


@router.post("/api/cart/get_quantity")
async def get_quantity(data: dict, db: AsyncSession = Depends(get_db)):
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    quantity = await cart_crud.get_quantity(db, user_id, item_id)
    return {"quantity": quantity}


@router.post("/api/cart/update_quantity")
async def update_quantity(data: dict, db: AsyncSession = Depends(get_db)):
    user_id = data.get('user_id')
    item_id = data.get('item_id')
    action = data.get('action')  # "increase" or "decrease"

    if action not in ["increase", "decrease"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    new_quantity = await cart_crud.update_quantity(db, user_id, item_id, action)
    return {"quantity": new_quantity}


@router.post("/api/cart/delete_item")
async def delete_cart_item(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Удаление товара из корзины пользователя.
    """
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Invalid input")

    # Удаляем товар из корзины
    await cart_crud.delete_cart_item(db, user_id, item_id)
    return {"status": "success"}


@router.post("/api/cart/remove_item")
async def remove_item_from_cart(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Удаление товара из корзины, если количество стало 0.
    """
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Invalid input")

    # Удаляем товар из корзины
    await cart_crud.delete_cart_item(db, user_id, item_id)
    return {"status": "success"}


@router.post("/api/cart/checkout")
async def checkout_cart(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Закрытие корзины пользователя.
    """
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    await cart_crud.checkout_cart(db, user_id)
    return {"status": "success"}
