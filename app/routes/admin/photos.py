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

router = APIRouter(prefix="/admin/albums/photos", tags=["Photos"])
templates = Jinja2Templates(directory="app/templates/admin")
logger = logging.getLogger("app.routes.admin.photos")



