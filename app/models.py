from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    price = Column(Float)
    brand = Column(String)
    model = Column(String)
    category = Column(String)
    sku = Column(String)
    stock_quantity = Column(Integer)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    marketplace = Column(String)
    status = Column(String)
    total_amount = Column(Float)
    customer_name = Column(String)
    customer_email = Column(String)
    order_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())