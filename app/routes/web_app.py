from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud import album_crud, user_crud
from app.utils.db import get_db
from fastapi.templating import Jinja2Templates
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def get_catalog(request: Request, db: AsyncSession = Depends(get_db)):
    # Запрашиваем все альбомы из базы данных
    albums = await album_crud.get_all_albums(db)

    # Передаем список альбомов в шаблон
    return templates.TemplateResponse("index.html", {"request": request, "albums": albums})


@router.post("/register_user")
async def register_user(request: Request, db: AsyncSession = Depends(get_db)):
    user_data = await request.json()
    logging.info(f"Received user data: {user_data}")
    await user_crud.add_user_if_not_exists(db, user_data)
    return {"status": "User registered successfully"}