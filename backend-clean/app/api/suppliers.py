"""
Suppliers API endpoints for the Hotel Procurement System
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.supplier import Supplier, SupplierCreate, SupplierUpdate

router = APIRouter()

@router.get("/", response_model=List[Supplier])
async def get_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all suppliers"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, name, code, contact_person, email, phone, address, city, country,
               tax_number, payment_terms, credit_limit, currency, rating, is_active,
               created_at, updated_at
        FROM suppliers 
        WHERE is_active = true
        ORDER BY name
        LIMIT :limit OFFSET :skip
    """), {"limit": limit, "skip": skip})
    
    suppliers = []
    for row in result:
        suppliers.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "contact_person": row.contact_person,
            "email": row.email,
            "phone": row.phone,
            "address": row.address,
            "city": row.city,
            "country": row.country,
            "tax_number": row.tax_number,
            "payment_terms": row.payment_terms,
            "credit_limit": float(row.credit_limit) if row.credit_limit else None,
            "currency": row.currency,
            "rating": row.rating,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return suppliers

@router.get("/{supplier_id}", response_model=Supplier)
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific supplier by ID"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, name, code, contact_person, email, phone, address, city, country,
               tax_number, payment_terms, credit_limit, currency, rating, is_active,
               created_at, updated_at
        FROM suppliers 
        WHERE id = :supplier_id
    """), {"supplier_id": str(supplier_id)})
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    return {
        "id": str(row.id),
        "name": row.name,
        "code": row.code,
        "contact_person": row.contact_person,
        "email": row.email,
        "phone": row.phone,
        "address": row.address,
        "city": row.city,
        "country": row.country,
        "tax_number": row.tax_number,
        "payment_terms": row.payment_terms,
        "credit_limit": float(row.credit_limit) if row.credit_limit else None,
        "currency": row.currency,
        "rating": row.rating,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    }

@router.post("/", response_model=Supplier, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier"""
    # Check if user has permission (only managers and superusers)
    if current_user.role not in ['manager', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    import uuid
    
    new_id = str(uuid.uuid4())
    
    db.execute(text("""
        INSERT INTO suppliers (id, name, code, contact_person, email, phone, address, 
                             city, country, payment_terms, currency, rating)
        VALUES (:id, :name, :code, :contact_person, :email, :phone, :address, 
                :city, :country, :payment_terms, :currency, :rating)
    """), {
        "id": new_id,
        "name": supplier.name,
        "code": supplier.code,
        "contact_person": supplier.contact_person,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
        "city": supplier.city,
        "country": supplier.country,
        "payment_terms": supplier.payment_terms,
        "currency": supplier.currency,
        "rating": supplier.rating
    })
    db.commit()
    
    # Return the created supplier
    return await get_supplier(UUID(new_id), db, current_user)
