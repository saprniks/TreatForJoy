from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud import album_crud, user_crud, item_crud, photo_crud
from app.utils.db import get_db
from fastapi.templating import Jinja2Templates
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def get_catalog(request: Request, db: AsyncSession = Depends(get_db)):
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
    return templates.TemplateResponse("index.html", {"request": request, "albums": albums, "items": filtered_items})


@router.get("/album/{album_id}", response_class=HTMLResponse)
async def view_album(album_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # Retrieve the album and its items by album_id
    album = await album_crud.get_album_by_id(db, album_id)
    items = await item_crud.get_items_by_album_id(db, album_id)

    # Добавляем к каждой item поле photo с display_order = 1
    for item in items:
        photo = await photo_crud.get_first_photo_for_item(db, item.id)
        item.photo_url = photo.url

    # Render album.html with the album and items data
    return templates.TemplateResponse("album.html", {"request": request, "album": album, "items": items})


# Регистрация пользователя
@router.post("/register_user")
async def register_user(request: Request, db: AsyncSession = Depends(get_db)):
    # Лог подтверждения получения запроса
    logging.info("Received POST request to /register_user")

    # Получаем данные пользователя из запроса
    user_data = await request.json()
    logging.info(f"Received user data: {user_data}")

    # Вызываем функцию для проверки и добавления пользователя, если он не существует
    await user_crud.add_user_if_not_exists(db, user_data)

    return {"status": "User registered successfully"}
