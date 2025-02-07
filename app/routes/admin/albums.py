from fastapi import APIRouter, Depends, Form, Request, HTTPException, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete, update
from app.models.models import Album, Item, Photo
from app.routes.admin.admin import manager
from app.utils.db import get_db
import logging
import os
from supabase import create_client, Client
from mimetypes import guess_type
import json
from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")  # Используем Service Role Key
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase configuration is missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(prefix="/admin/albums", tags=["Albums"])
templates = Jinja2Templates(directory="app/templates/admin")
logger = logging.getLogger("app.routes.admin.albums")


# Route for photo upload
@router.post("/photos/upload")
async def upload_photo(file: UploadFile, user=Depends(manager)):
    try:
        # Ensure file is uploaded
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Read file content
        file_content = await file.read()
        file_name = file.filename

        # Determine MIME type
        mime_type, _ = guess_type(file_name)
        if not mime_type:
            mime_type = "application/octet-stream"  # Fallback if the type is unknown
        logger.info(f"Determined MIME type: {mime_type} for file {file_name}")


        # Upload to Supabase with MIME type
        response = supabase.storage.from_("photos").upload(
            file_name, file_content, {"content-type": mime_type}
        )

        # Check if the upload was successful
        if not response:
            logger.error("Failed to upload file to Supabase storage")
            raise HTTPException(status_code=400, detail="File upload failed")

        # Generate public URL
        public_url = supabase.storage.from_("photos").get_public_url(file_name)

        if not public_url:  # Ensure public_url is not empty or invalid
            logger.error(f"Failed to generate public URL: {public_url}")
            raise HTTPException(status_code=500, detail="Failed to generate photo URL")

        # Log success and return public URL
        logger.info(f"Photo uploaded successfully. Public URL: {public_url}")
        return JSONResponse(status_code=200, content={"photo_url": public_url})
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Route for photo delete
@router.delete("/photos/delete/{photo_id}")
async def delete_photo(photo_id: int, request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    logger.info(f"Received request to delete photo with ID: {photo_id}")
    try:
        # Получение данных из запроса
        #data = await request.json()
        #logger.debug(f"Request JSON data: {data}")

        #display_order = data.get("displayOrder")
        #if display_order is None:
        #    logger.error("Missing 'displayOrder' field in request body")
        #    raise HTTPException(status_code=422, detail="Missing 'displayOrder' field in request body")

        # Поиск изделия по ID
        photo_query = select(Photo).where(Photo.id == photo_id)
        photo_result = await db.execute(photo_query)
        photo = photo_result.scalars().first()

        if not photo:
            logger.error(f"Photo with ID {photo_id} not found")
            raise HTTPException(status_code=404, detail="Photo not found")

        logger.info(f"Found item: {photo.id}")

        # Сдвиг display_order у других изделий
        shift_query = select(Photo).where(
            Photo.item_id == photo.item_id,
            Photo.display_order > photo.display_order
        )
        shift_result = await db.execute(shift_query)
        photos_to_shift = shift_result.scalars().all()

        logger.debug(f"Photos to update (decrement display_order): {[i.display_order for i in photos_to_shift]}")

        for photo_to_shift in photos_to_shift:
            photo_to_shift.display_order -= 1
            db.add(photo_to_shift)
            logger.info(f"Updated photo {photo_to_shift.id}: new display_order {photo_to_shift.display_order}")

        # Удаление ВСЕХ фотографий с таким ID
        photo_query = select(Photo).where(Photo.id == photo_id)
        photo_result = await db.execute(photo_query)
        photos_to_delete = photo_result.scalars().all()

        logger.debug(f"Photos to delete: {[photo.url for photo in photos_to_delete]}")

        for photo in photos_to_delete:
            # Удаление фотографий из Supabase
            file_name = photo.url.split("/")[-1].rstrip("?")
            response = supabase.storage.from_("photos").remove([file_name])

            if response and isinstance(response, list) and response[0].get("error"):
                logger.error(f"Error deleting photo from Supabase: {file_name}, error: {response[0]['error']}")
            else:
                logger.info(f"Deleted photo from Supabase: {file_name}")

            # Удаление записи о фото
            await db.delete(photo)

        # Сохранение изменений в базе данных
        await db.commit()
        logger.info(f"Changes committed successfully")

        return {"success": True}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during photo deletion: {e}")
        await db.rollback()  # Откат транзакции при ошибке
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Список альбомов
@router.get("/")
async def list_albums(request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    query = select(Album).order_by(Album.display_order)
    result = await db.execute(query)
    albums = result.scalars().all()
    return templates.TemplateResponse("albums/list.html", {"request": request, "albums": albums})


@router.post("/create")
async def create_album(
    title: str = Form(...),
    notes: str = Form(""),
    display_order: int = Form(0),
    is_visible: bool = Form(True),
    is_available_to_order: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    user=Depends(manager),
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
async def edit_album_form(album_id: int, request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Получаем альбом по ID
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()

    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Подсчитываем общее количество альбомов
    count_query = select(func.count()).select_from(Album)
    count_result = await db.execute(count_query)
    max_display_order = count_result.scalar()

    # Получаем связанные элементы (items) с первым фото (display_order=1)
    items_query = (
        select(
            Item,
            Photo.url.label("photo_url")
        )
        .outerjoin(Photo, (Photo.item_id == Item.id) & (Photo.display_order == 1))
        .where(Item.album_id == album_id)
        .order_by(Item.display_order)
    )
    items_result = await db.execute(items_query)
    items = [
        {
            "id": item.id,
            "title": item.title,
            "sku": item.sku,
            "price": item.price,
            "display_order": item.display_order,
            "is_available_to_order": item.is_available_to_order,
            "is_visible": item.is_visible,
            "photo_url": photo_url,
        }
        for item, photo_url in items_result.all()
    ]

    return templates.TemplateResponse(
        "albums/edit.html",
        {"request": request, "album": album, "items": items, "max_display_order": max_display_order}
    )


@router.post("/{album_id}/edit")
async def edit_album(
    album_id: int,
    title: str = Form(...),
    display_order: int = Form(...),
    is_visible: bool = Form(True),
    is_available_to_order: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    user=Depends(manager),
):
    # Получаем текущий альбом
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()

    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Проверяем, изменилось ли состояние `is_available_to_order`
    if album.is_available_to_order != is_available_to_order:
        # Обновляем состояние всех изделий, связанных с альбомом
        items_query = select(Item).where(Item.album_id == album_id)
        items_result = await db.execute(items_query)
        items = items_result.scalars().all()

        for item in items:
            item.is_available_to_order = is_available_to_order

    # Обновляем основные свойства альбома
    album.title = title
    album.is_visible = is_visible
    album.is_available_to_order = is_available_to_order

    # Обновляем порядок отображения, если он изменился
    old_display_order = album.display_order
    if old_display_order != display_order:
        count_query = select(func.count()).select_from(Album)
        count_result = await db.execute(count_query)
        total_albums = count_result.scalar()

        if display_order < 1 or display_order > total_albums:
            raise HTTPException(status_code=400, detail="Invalid display_order value.")

        if display_order > old_display_order:
            shift_query = (
                select(Album)
                .where(Album.display_order > old_display_order, Album.display_order <= display_order)
                .order_by(Album.display_order)
            )
            shift_result = await db.execute(shift_query)
            albums_to_shift = shift_result.scalars().all()
            for a in albums_to_shift:
                a.display_order -= 1
        elif display_order < old_display_order:
            shift_query = (
                select(Album)
                .where(Album.display_order >= display_order, Album.display_order < old_display_order)
                .order_by(Album.display_order)
            )
            shift_result = await db.execute(shift_query)
            albums_to_shift = shift_result.scalars().all()
            for a in albums_to_shift:
                a.display_order += 1

        album.display_order = display_order

    # Сохраняем изменения
    await db.commit()

    return RedirectResponse("/admin/albums", status_code=302)

#
# # Удаление альбома
# @router.get("/{album_id}/delete")
# async def delete_album(album_id: int, db: AsyncSession = Depends(get_db)):
#     query = select(Album).where(Album.id == album_id)
#     result = await db.execute(query)
#     album = result.scalars().first()
#     if not album:
#         raise HTTPException(status_code=404, detail="Album not found")
#     await db.delete(album)
#     await db.commit()
#     return RedirectResponse("/admin/albums", status_code=302)


# Переключение видимости альбома
@router.post("/{album_id}/toggle-visibility")
async def toggle_visibility(album_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
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
async def toggle_availability(album_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
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
async def move_up(album_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
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
async def move_down(album_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
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


@router.get("/{album_id}/add-item")
async def add_item_form(album_id: int, request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Проверяем, существует ли альбом
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()

    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Считаем количество текущих изделий в альбоме
    items_count_query = select(func.count()).select_from(Item).where(Item.album_id == album_id)
    items_count_result = await db.execute(items_count_query)
    items_count = items_count_result.scalar()

    # Возвращаем форму для добавления изделия
    return templates.TemplateResponse(
        "albums/add_item.html",
        {
            "request": request,
            "album": album,
            "items_count": items_count  # Передаем количество изделий
        },
    )


@router.post("/{album_id}/add-item")
async def add_item(
    album_id: int,
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sku: str = Form(None),  # Добавлено поле SKU
    display_order: int = Form(...),  # Порядковый номер передается в запросе
    is_available_to_order: bool = Form(True),
    photos: str = Form(...),  # JSON-строка с URL и порядком фото
    db: AsyncSession = Depends(get_db),
    user=Depends(manager),
):
    # Проверяем, существует ли альбом
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalars().first()

    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Сдвигаем порядковые номера для существующих изделий
    update_query = (
        select(Item)
        .where(Item.album_id == album_id, Item.display_order >= display_order)
        .order_by(Item.display_order.desc())
    )
    items_to_update = await db.execute(update_query)
    items = items_to_update.scalars().all()

    for item in items:
        item.display_order += 1  # Сдвигаем порядок на +1
        db.add(item)

    # Создаем новое изделие
    new_item = Item(
        title=title,
        description=description,
        price=price,
        sku=sku,  # Сохраняем SKU
        display_order=display_order,  # Устанавливаем заданный порядковый номер
        is_available_to_order=is_available_to_order,
        album_id=album_id,
    )
    db.add(new_item)
    await db.flush()  # Получаем ID изделия перед фиксацией

    # Добавление фотографий
    photo_data = json.loads(photos)
    for photo in photo_data:
        new_photo = Photo(
            item_id=new_item.id,
            url=photo["url"],
            display_order=photo["display_order"],
        )
        db.add(new_photo)

    # Сохраняем изменения
    await db.commit()
    return RedirectResponse(f"/admin/albums/{album_id}/edit", status_code=302)


@router.post("/items/{item_id}/toggle-visibility")
async def toggle_item_visibility(item_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Получаем изделие по ID
    query = select(Item).where(Item.id == item_id)
    result = await db.execute(query)
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Переключаем состояние видимости
    item.is_visible = not item.is_visible

    # Сохраняем изменения
    await db.commit()

    return {"success": True}


@router.post("/items/{item_id}/toggle-availability")
async def toggle_item_availability(item_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Получение изделия по ID
    query = select(Item).where(Item.id == item_id)
    result = await db.execute(query)
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Переключаем состояние доступности для заказа
    item.is_available_to_order = not item.is_available_to_order
    await db.commit()

    return {"success": True, "is_available_to_order": item.is_available_to_order}


@router.post("/items/{item_id}/move-up")
async def move_item_up(item_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Найти текущее изделие
    query = select(Item).where(Item.id == item_id)
    result = await db.execute(query)
    current_item = result.scalars().first()

    if not current_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Проверить, не первое ли это изделие
    if current_item.display_order == 1:
        return {"success": False, "message": "Item is already at the top"}

    # Найти предыдущее изделие
    prev_item_query = (
        select(Item)
        .where(
            Item.album_id == current_item.album_id,
            Item.display_order == current_item.display_order - 1
        )
    )
    prev_result = await db.execute(prev_item_query)
    prev_item = prev_result.scalars().first()

    if not prev_item:
        raise HTTPException(status_code=404, detail="Previous item not found")

    # Обновить display_order у обоих изделий
    current_item.display_order -= 1
    prev_item.display_order += 1

    await db.commit()
    return {"success": True}


@router.post("/items/{item_id}/move-down")
async def move_item_down(item_id: int, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Найти текущее изделие
    query = select(Item).where(Item.id == item_id)
    result = await db.execute(query)
    current_item = result.scalars().first()

    if not current_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Найти максимальный display_order для текущего альбома
    max_order_query = (
        select(func.max(Item.display_order))
        .where(Item.album_id == current_item.album_id)
    )
    max_order_result = await db.execute(max_order_query)
    max_order = max_order_result.scalar()

    # Проверить, не последнее ли это изделие
    if current_item.display_order == max_order:
        return {"success": False, "message": "Item is already at the bottom"}

    # Найти следующее изделие
    next_item_query = (
        select(Item)
        .where(
            Item.album_id == current_item.album_id,
            Item.display_order == current_item.display_order + 1
        )
    )
    next_result = await db.execute(next_item_query)
    next_item = next_result.scalars().first()

    if not next_item:
        raise HTTPException(status_code=404, detail="Next item not found")

    # Обновить display_order у обоих изделий
    current_item.display_order += 1
    next_item.display_order -= 1

    await db.commit()
    return {"success": True}


@router.post("/items/{item_id}/delete")
async def delete_item(item_id: int, request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    logger.info(f"Received request to delete item with ID: {item_id}")
    try:
        # Получение данных из запроса
        data = await request.json()
        logger.debug(f"Request JSON data: {data}")

        display_order = data.get("displayOrder")
        if display_order is None:
            logger.error("Missing 'displayOrder' field in request body")
            raise HTTPException(status_code=422, detail="Missing 'displayOrder' field in request body")

        # Поиск изделия по ID
        item_query = select(Item).where(Item.id == item_id)
        item_result = await db.execute(item_query)
        item = item_result.scalars().first()

        if not item:
            logger.error(f"Item with ID {item_id} not found")
            raise HTTPException(status_code=404, detail="Item not found")

        logger.info(f"Found item: {item.title}, display_order: {item.display_order}")

        # Сдвиг display_order у других изделий
        shift_query = select(Item).where(
            Item.album_id == item.album_id,
            Item.display_order > display_order
        )
        shift_result = await db.execute(shift_query)
        items_to_shift = shift_result.scalars().all()

        logger.debug(f"Items to update (decrement display_order): {[i.display_order for i in items_to_shift]}")

        for item_to_shift in items_to_shift:
            item_to_shift.display_order -= 1
            db.add(item_to_shift)
            logger.info(f"Updated item {item_to_shift.id}: new display_order {item_to_shift.display_order}")

        # Удаление фотографий, связанных с изделием
        photo_query = select(Photo).where(Photo.item_id == item_id)
        photo_result = await db.execute(photo_query)
        photos_to_delete = photo_result.scalars().all()

        logger.debug(f"Photos to delete: {[photo.url for photo in photos_to_delete]}")

        for photo in photos_to_delete:
            # Удаление фотографий из Supabase
            file_name = photo.url.split("/")[-1].rstrip("?")
            response = supabase.storage.from_("photos").remove([file_name])

            if response and isinstance(response, list) and response[0].get("error"):
                logger.error(f"Error deleting photo from Supabase: {file_name}, error: {response[0]['error']}")
            else:
                logger.info(f"Deleted photo from Supabase: {file_name}")

            # Удаление записи о фото
            await db.delete(photo)

        # Удаление изделия
        await db.delete(item)
        logger.info(f"Deleted item with ID: {item_id}")

        # Сохранение изменений в базе данных
        await db.commit()
        logger.info(f"Changes committed successfully")

        return {"success": True}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during item deletion: {e}")
        await db.rollback()  # Откат транзакции при ошибке
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/items/{item_id}/edit")
async def edit_item_form(item_id: int, request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    # Получаем изделие по ID
    query = select(Item).where(Item.id == item_id)
    result = await db.execute(query)
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Получаем фотографии изделия
    photo_query = select(Photo).where(Photo.item_id == item_id).order_by(Photo.display_order)
    photo_result = await db.execute(photo_query)
    photos = photo_result.scalars().all()

    # Преобразуем фотографии в сериализуемый формат
    serialized_photos = [
        {
            "id": photo.id,
            "url": photo.url,
            "description": photo.description,
            "display_order": photo.display_order,
        }
        for photo in photos
    ]

    # Получаем общее количество изделий в альбоме
    count_query = select(func.count()).select_from(Item).where(Item.album_id == item.album_id)
    count_result = await db.execute(count_query)
    total_items = count_result.scalar()

    return templates.TemplateResponse(
        "albums/edit_item.html",
        {
            "request": request,
            "item": item,
            "photos": serialized_photos,  # Передаём сериализованные фотографии
            "total_items": total_items,
        },
    )


@router.post("/items/{item_id}/edit")
async def edit_item(
    item_id: int,
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sku: str = Form(None),
    display_order: int = Form(...),
    is_available_to_order: str = Form("false"),
    is_visible: str = Form("false"),
    photos: str = Form(...),  # JSON-строка с информацией о фотографиях
    db: AsyncSession = Depends(get_db),
    user=Depends(manager),
):
    try:
        # Преобразуем значения флажков в булев тип
        is_available_to_order = is_available_to_order.lower() == "true"
        is_visible = is_visible.lower() == "true"

        # Получаем изделие по ID
        query = select(Item).where(Item.id == item_id)
        result = await db.execute(query)
        item = result.scalars().first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Проверяем, изменился ли порядок отображения (`display_order`)
        old_display_order = item.display_order
        if display_order != old_display_order:
            # Пересчёт порядков отображения для остальных изделий
            items_query = select(Item).where(Item.album_id == item.album_id)
            items_result = await db.execute(items_query)
            items = items_result.scalars().all()

            if display_order > old_display_order:
                for i in items:
                    if old_display_order < i.display_order <= display_order:
                        i.display_order -= 1
            elif display_order < old_display_order:
                for i in items:
                    if display_order <= i.display_order < old_display_order:
                        i.display_order += 1

        # Обновляем свойства изделия
        item.title = title
        item.description = description
        item.price = price
        item.sku = sku
        item.display_order = display_order
        item.is_available_to_order = is_available_to_order
        item.is_visible = is_visible

        # Обновление фотографий
        photo_data = json.loads(photos)  # Преобразуем JSON-строку в список словарей
        existing_photos_query = select(Photo).where(Photo.item_id == item_id)
        existing_photos = (await db.execute(existing_photos_query)).scalars().all()

        # Сохраняем новые или изменяем существующие фотографии
        for photo in photo_data:
            matching_photo = next((p for p in existing_photos if p.id == photo.get("id")), None)
            if matching_photo:
                # Обновляем существующую фотографию
                matching_photo.url = photo["url"]
                matching_photo.display_order = int(photo["display_order"])
            else:
                # Добавляем новую фотографию
                new_photo = Photo(
                    item_id=item.id,
                    url=photo["url"],
                    display_order=int(photo["display_order"]),
                )
                db.add(new_photo)

        # Удаляем фотографии, которые больше не указаны
        for photo in existing_photos:
            if not any(p.get("id") == photo.id for p in photo_data):
                await db.delete(photo)

        # Сохраняем изменения
        await db.commit()

        return RedirectResponse(f"/admin/albums/{item.album_id}/edit", status_code=302)
    except Exception as e:
        logger.error(f"Error editing item: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/create")
async def create_album_form(request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):

    # Подсчитываем общее количество альбомов
    count_query = select(func.count()).select_from(Album)
    count_result = await db.execute(count_query)
    max_display_order = count_result.scalar() + 1
    logger.info(f"Max display order: {max_display_order}")

    # Передаем max_display_order в шаблон
    return templates.TemplateResponse("albums/create.html", {"request": request, "max_display_order": max_display_order})


@router.post("/create")
async def create_album(
    title: str = Form(...),
    display_order: int = Form(...),
    notes: str = Form(""),
    is_visible: bool = Form(True),
    is_available_to_order: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    user=Depends(manager),
):
    try:
        # Сдвигаем порядок отображения существующих альбомов
        shift_query = (
            select(Album)
            .where(Album.display_order >= display_order)
            .order_by(Album.display_order.desc())
        )
        result = await db.execute(shift_query)
        albums_to_shift = result.scalars().all()

        for album in albums_to_shift:
            album.display_order += 1
            db.add(album)

        # Создаём новый альбом
        new_album = Album(
            title=title,
            notes=notes,
            display_order=display_order,
            is_visible=is_visible,
            is_available_to_order=is_available_to_order,
        )
        db.add(new_album)
        await db.flush()  # Получаем ID альбома до коммита

        # Сохраняем изменения
        await db.commit()

        # Редирект на страницу редактирования нового альбома
        return RedirectResponse(f"/admin/albums/{new_album.id}/edit", status_code=302)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating album: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
