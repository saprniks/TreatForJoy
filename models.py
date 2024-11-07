from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, DateTime, Table, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Таблица для связи многие-ко-многим между Users и Items для избранного
favorites_table = Table(
    'favorites',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('item_id', Integer, ForeignKey('items.id'), nullable=False)
)

# Таблица для связи многие-ко-многим между Users и Items для корзины
class Cart(Base):
    __tablename__ = 'cart'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    checkout_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Связи
    user = relationship("User", back_populates="cart_items")
    item = relationship("Item", back_populates="cart_entries")

# Таблица пользователей
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Связи
    favorites = relationship("Item", secondary=favorites_table, back_populates="favorited_by")
    cart_items = relationship("Cart", back_populates="user")

# Таблица альбомов
class Album(Base):
    __tablename__ = 'albums'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    display_order = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    # Связи
    items = relationship("Item", back_populates="album")

# Таблица изделий
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    display_order = Column(Integer, default=0)
    album_id = Column(Integer, ForeignKey('albums.id'))

    # Связи
    album = relationship("Album", back_populates="items")
    photos = relationship("Photo", back_populates="item")
    favorited_by = relationship("User", secondary=favorites_table, back_populates="favorites")
    cart_entries = relationship("Cart", back_populates="item")

# Таблица фотографий
class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)

    # Связи
    item = relationship("Item", back_populates="photos")
