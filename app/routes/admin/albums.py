from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Album, Item
from app.utils.db import get_db
import logging

router = APIRouter(prefix="/admin/albums", tags=["Albums"])
templates = Jinja2Templates(directory="app/templates/admin")
logger = logging.getLogger("app.routes.admin.albums")


# Список альбомов
@router.get("/")
async def list_albums(request: Request, db: AsyncSession = Depends(get_db)):
    query = select(Album).order_by(Album.display_order)
    result = await db.execute(query)
    albums = result.scalars().all()
    return templates.TemplateResponse("albums/list.html", {"request": request, "albums": albums})


# Создание альбома
@router.get("/create")
async def create_album_form(request: Request):
    return templates.TemplateResponse("albums/create.html", {"request": request})


@router.post("/create")
async def create_album(
    title: str = Form(...),
    notes: str = Form(""),
    display_order: int = Form(0),
    is_visible: bool = Form(True),
    is_available_to_order: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    new_album = Album(
        title=title,
        notes=notes,
        display_order=display_order,
        is_visible=is_visible,
        is_available_to_order=is_available_to_order,
    )
    db.add(new_album)
    await db.commit()
    return RedirectResponse("/admin/albums", status_code=302)


# Редактирование альбома
@router.get("/{album_id}/edit")
async def edit_album_form(album_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return templates.TemplateResponse("albums/edit.html", {"request": request, "album": album})


@router.post("/{album_id}/edit")
async def edit_album(
    album_id: int,
    title: str = Form(...),
    notes: str = Form(""),
    display_order: int = Form(0),
    is_visible: bool = Form(True),
    is_available_to_order: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    album.title = title
    album.notes = notes
    album.display_order = display_order
    album.is_visible = is_visible
    album.is_available_to_order = is_available_to_order

    await db.commit()
    return RedirectResponse("/admin/albums", status_code=302)


# Удаление альбома
@router.get("/{album_id}/delete")
async def delete_album(album_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    await db.delete(album)
    await db.commit()
    return RedirectResponse("/admin/albums", status_code=302)


# Переключение видимости альбома
@router.post("/{album_id}/toggle-visibility")
async def toggle_visibility(album_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    album.is_visible = not album.is_visible
    await db.commit()
    return {"success": True}


# Переключение возможности заказа альбома
@router.post("/{album_id}/toggle-availability")
async def toggle_availability(album_id: int, db: AsyncSession = Depends(get_db)):
    # Получение альбома по ID
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()

    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Переключаем состояние is_available_to_order у альбома
    album.is_available_to_order = not album.is_available_to_order

    # Обновляем состояние is_available_to_order для всех изделий в альбоме
    update_items_query = select(Item).where(Item.album_id == album_id)
    items_result = await db.execute(update_items_query)
    items = items_result.scalars().all()

    for item in items:
        item.is_available_to_order = album.is_available_to_order

    # Сохраняем изменения в базе данных
    await db.commit()

    return {"success": True}


# Перемещение альбома вверх
@router.post("/{album_id}/move-up")
async def move_up(album_id: int, db: AsyncSession = Depends(get_db)):
    # Найти текущий альбом
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    current_album = result.scalars().first()

    if not current_album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Проверить, не первый ли это альбом
    if current_album.display_order == 1:
        return {"success": False, "message": "Album is already at the top"}

    # Найти предыдущий альбом
    prev_album_query = select(Album).where(Album.display_order == current_album.display_order - 1)
    prev_result = await db.execute(prev_album_query)
    prev_album = prev_result.scalars().first()

    if not prev_album:
        raise HTTPException(status_code=404, detail="Previous album not found")

    # Обновить display_order у обоих альбомов
    current_album.display_order -= 1
    prev_album.display_order += 1

    await db.commit()
    return {"success": True}


# Перемещение альбома вниз
@router.post("/{album_id}/move-down")
async def move_down(album_id: int, db: AsyncSession = Depends(get_db)):
    # Найти текущий альбом
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    current_album = result.scalars().first()

    if not current_album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Найти максимальный display_order для проверки
    max_order_query = select(Album.display_order).order_by(Album.display_order.desc()).limit(1)
    max_order_result = await db.execute(max_order_query)
    max_order = max_order_result.scalar()

    # Проверить, не является ли альбом последним
    if current_album.display_order == max_order:
        return {"success": False, "message": "Album is already at the bottom"}

    # Найти следующий альбом
    next_album_query = select(Album).where(Album.display_order == current_album.display_order + 1)
    next_result = await db.execute(next_album_query)
    next_album = next_result.scalars().first()

    if not next_album:
        raise HTTPException(status_code=404, detail="Next album not found")

    # Обновить display_order у обоих альбомов
    current_album.display_order += 1
    next_album.display_order -= 1

    await db.commit()
    return {"success": True}

