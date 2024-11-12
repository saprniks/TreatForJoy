from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/catalog")
async def get_catalog(request: Request):
    # Здесь пока что простой вывод "Hello world"
    return templates.TemplateResponse("index.html", {"request": request})
