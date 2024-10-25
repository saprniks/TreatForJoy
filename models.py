from flask_sqlalchemy import SQLAlchemy
from config import DATABASE_URL
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)


# Модель для пользователей
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    avatar_url = db.Column(db.String(200), nullable=True)


# Модель для фотографий
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)


# Модель для комментариев
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())


# Функция для создания всех таблиц
def create_tables():
    with app.app_context():
        db.create_all()
