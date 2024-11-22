from passlib.context import CryptContext
from app.models.models import AdminUser
from app.utils.db import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

# Создаем первого администратора
admin = AdminUser(username="admin", password_hash=pwd_context.hash("your_password"))
db.add(admin)
db.commit()
db.close()

print("Администратор создан!")
