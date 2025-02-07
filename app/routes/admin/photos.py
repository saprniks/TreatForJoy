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

@router.post("/items/{item_id}/delete")
async def delete_photo(photo_id: int, request: Request, db: AsyncSession = Depends(get_db), user=Depends(manager)):
    logger.info(f"Received request to delete photo with ID: {photo_id}")
    try:
        # Получение данных из запроса
        data = await request.json()
        logger.debug(f"Request JSON data: {data}")

        display_order = data.get("displayOrder")
        if display_order is None:
            logger.error("Missing 'displayOrder' field in request body")
            raise HTTPException(status_code=422, detail="Missing 'displayOrder' field in request body")

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

