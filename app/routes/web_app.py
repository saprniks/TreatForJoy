from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud import album_crud, user_crud, item_crud, photo_crud
from app.utils.db import get_db
from fastapi.templating import Jinja2Templates
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

    # Отбираем изделия с display_order <= 3
    filtered_items = [item for item in items_all if item.display_order <= 3]

    # Добавляем к каждой item поле photo с display_order = 1
    for item in filtered_items:
        photo = await photo_crud.get_first_photo_for_item(db, item.id)
        item.photo_url = photo.url

    # Передаем список альбомов и отфильтрованные изделия в шаблон
    return templates.TemplateResponse("index.html", {"request": request, "albums": albums, "items": filtered_items, "user_id": user_id})


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

    # Add a photo with display_order = 1 to each item
    for item in items:
        photo = await photo_crud.get_first_photo_for_item(db, item.id)
        item.photo_url = photo.url

    # Render album.html with the album, items, and user_id
    return templates.TemplateResponse(
        "album.html", {"request": request, "album": album, "items": items, "user_id": user_id}
    )


@router.get("/item/{item_id}", response_class=HTMLResponse)
async def view_item(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # Retrieve the item and its photos by item_id
    item = await item_crud.get_item_by_id(db, item_id)
    photos = await photo_crud.get_photos_for_item(db, item_id)

    # Render item.html with the photos and item data
    return templates.TemplateResponse("item.html", {"request": request, "item": item, "photos": photos})


# Регистрация пользователя
# @router.post("/register_user")
# async def register_user(request: Request, db: AsyncSession = Depends(get_db)):
#     # Лог подтверждения получения запроса
#     logging.info("Received POST request to /register_user")
#
#     # Получаем данные пользователя из запроса
#     user_data = await request.json()
#     logging.info(f"Received user data: {user_data}")
#
#     # Вызываем функцию для проверки и добавления пользователя, если он не существует
#     user = await user_crud.add_user_if_not_exists(db, user_data)
#
#     await get_catalog(user_id=user.id, request=request, db=db)
#
#
#
