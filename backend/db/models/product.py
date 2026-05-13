from sqlalchemy import Column, String, Float, Boolean, Text, ARRAY, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    part_number = Column(String(20), unique=True, nullable=False, index=True)
    manufacturer_part_number = Column(String(50))
    name = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(20), nullable=False)  # refrigerator | dishwasher
    brand = Column(String(50))
    price = Column(Float)
    in_stock = Column(Boolean, default=True)
    image_url = Column(Text)
    product_url = Column(Text)
    symptom_tags = Column(JSON)  # list of strings
    scraped_at = Column(DateTime, default=datetime.utcnow)


class ModelCompatibility(Base):
    __tablename__ = "model_compatibility"

    part_number = Column(String(20), primary_key=True)
    model_number = Column(String(50), primary_key=True, index=True)


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(255))
    status = Column(String(50))
    items = Column(JSON)
    total = Column(Float)
    estimated_delivery = Column(String)
    tracking_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class CartSession(Base):
    __tablename__ = "cart_sessions"

    session_id = Column(String(100), primary_key=True)
    items = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    session_id = Column(String(100), primary_key=True)
    history = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
