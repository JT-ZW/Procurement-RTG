"""
Product schemas for the Hotel Procurement System
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ProductBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    unit_of_measure: str = "pieces"
    standard_cost: Optional[float] = None
    currency: str = "USD"
    minimum_stock_level: int = 0
    maximum_stock_level: int = 1000
    reorder_point: int = 10
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    unit_of_measure: Optional[str] = None
    standard_cost: Optional[float] = None
    currency: Optional[str] = None
    minimum_stock_level: Optional[int] = None
    maximum_stock_level: Optional[int] = None
    reorder_point: Optional[int] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: str
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
