"""
Purchase Requisition schemas for the Hotel Procurement System
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
from uuid import UUID

class PurchaseRequisitionItemBase(BaseModel):
    product_id: Optional[UUID] = None
    product_name: str
    product_description: Optional[str] = None
    quantity: float
    unit_of_measure: str
    estimated_unit_price: Optional[float] = None
    estimated_total_price: Optional[float] = None
    currency: str = "USD"
    specifications: Optional[str] = None
    notes: Optional[str] = None

class PurchaseRequisitionItem(PurchaseRequisitionItemBase):
    id: str
    product_catalog_name: Optional[str] = None
    product_code: Optional[str] = None

    class Config:
        from_attributes = True

class PurchaseRequisitionBase(BaseModel):
    title: str
    description: Optional[str] = None
    department: Optional[str] = None
    priority: str = "medium"  # low, medium, high, urgent
    required_date: date
    total_estimated_amount: float = 0.0
    currency: str = "USD"

class PurchaseRequisitionCreate(PurchaseRequisitionBase):
    items: Optional[List[PurchaseRequisitionItemBase]] = []

class PurchaseRequisitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    required_date: Optional[date] = None
    total_estimated_amount: Optional[float] = None
    status: Optional[str] = None
    approval_notes: Optional[str] = None

class PurchaseRequisition(PurchaseRequisitionBase):
    id: str
    requisition_number: str
    requested_by: str
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    unit_id: str
    unit_name: Optional[str] = None
    status: str
    requested_date: Optional[str] = None
    approval_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approver_name: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: Optional[List[PurchaseRequisitionItem]] = []

    class Config:
        from_attributes = True
