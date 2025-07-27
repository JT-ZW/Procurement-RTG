"""
Supplier schemas for the Hotel Procurement System
"""
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class SupplierBase(BaseModel):
    name: str
    code: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    tax_number: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    currency: str = "USD"
    rating: Optional[int] = None
    is_active: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    tax_number: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[int] = None
    is_active: Optional[bool] = None

class Supplier(SupplierBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
