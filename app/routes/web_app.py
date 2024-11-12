from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Album
from app.utils.db import get_db
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def get_catalog(request: Request, db: AsyncSession = Depends(get_db)):
    # Запрашиваем все альбомы из базы данных
    result = await db.execute(select(Album))
    albums = result.scalars().all()

    # Передаем список альбомов в шаблон
    return templates.TemplateResponse("index.html", {"request": request, "albums": albums})
