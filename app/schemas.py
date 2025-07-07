from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    stock_quantity: Optional[int] = 0

class ProductCreate(ProductBase):
    anymarket_id: str

class Product(ProductBase):
    id: int
    anymarket_id: str
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    marketplace: str
    status: str
    total_amount: float
    customer_name: str
    customer_email: str
    order_date: datetime

class OrderCreate(OrderBase):
    anymarket_id: str

class Order(OrderBase):
    id: int
    anymarket_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True