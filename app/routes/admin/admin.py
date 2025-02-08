from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_login import LoginManager
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import AdminUser
from app.utils.db import get_db, SessionLocal  # Import SessionLocal
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta

# Настройки
load_dotenv()
SECRET = os.getenv("SECRET_KEY")
if not SECRET:
    raise ValueError("SECRET_KEY is not set in the environment.")

#manager = LoginManager(SECRET, token_url="/admin/login", use_cookie=True)
manager = LoginManager(SECRET, token_url="/admin/login", use_cookie=True, expires_in=timedelta(hours=12))
manager.cookie_name = "access-token"
templates = Jinja2Templates(directory="app/templates/admin")

# Хэширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Роутер для админки
router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger("app.routes.admin")
logger.setLevel(logging.DEBUG)

# Получение пользователя из базы данных
async def get_user(username: str, session: AsyncSession) -> AdminUser | None:
    logger.debug(f"Fetching user with username: {username}")
    query = select(AdminUser).where(AdminUser.username == username)
    result = await session.execute(query)
    user = result.scalars().first()
    logger.debug(f"User fetched: {user}")
    return user

# Callback для fastapi-login
@manager.user_loader()
async def load_user(username: str):
    logger.debug(f"Loading user for username: {username}")
    async with SessionLocal() as db_session:
        user = await get_user(username, db_session)
    if user:
        logger.debug(f"User loaded successfully: {user.username}")
    else:
        logger.warning(f"User not found for username: {username}")
    return user

# Маршрут логина
@router.get("/login")
async def login_page(request: Request):
    logger.debug("Login page accessed.")
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db_session: AsyncSession = Depends(get_db),
):
    logger.debug(f"Attempting login for username: {username}")
    user = await get_user(username, db_session)
    if not user or not pwd_context.verify(password, user.password_hash):
        logger.warning(f"Login failed: Incorrect credentials for user '{username}'.")
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials!"}
        )

    logger.info(f"User '{username}' successfully logged in.")
    access_token = manager.create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/admin", status_code=302)
    manager.set_cookie(response, access_token)
    logger.debug(f"Token set in cookie for user '{username}': {access_token}")
    return response

# Маршрут логаута
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    manager.set_cookie(response, None)
    logger.info("User logged out.")
    return response

# Главная страница админки
@router.get("/")
async def admin_dashboard(request: Request, user=Depends(manager)):
    if not user:
        logger.warning("Unauthorized access attempt to /admin.")
        raise HTTPException(status_code=401, detail="Unauthorized access. Please log in.")
    logger.debug(f"User {user.username} accessed admin dashboard.")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
