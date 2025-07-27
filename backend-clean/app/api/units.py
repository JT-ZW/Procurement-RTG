"""
Units API endpoints for the Hotel Procurement System
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_sync_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.unit import Unit, UnitCreate, UnitUpdate

router = APIRouter()

@router.get("/", response_model=List[Unit])
async def get_units(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Get all hotel units/properties"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, name, code, description, address, city, country, 
               is_active, created_at, updated_at
        FROM units 
        WHERE is_active = true
        ORDER BY name
        LIMIT :limit OFFSET :skip
    """), {"limit": limit, "skip": skip})
    
    units = []
    for row in result:
        units.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "description": row.description,
            "address": row.address,
            "city": row.city,
            "country": row.country,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return units

@router.get("/{unit_id}", response_model=Unit)
async def get_unit(
    unit_id: UUID,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific hotel unit by ID"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, name, code, description, address, city, country, 
               is_active, created_at, updated_at
        FROM units 
        WHERE id = :unit_id
    """), {"unit_id": str(unit_id)})
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    return {
        "id": str(row.id),
        "name": row.name,
        "code": row.code,
        "description": row.description,
        "address": row.address,
        "city": row.city,
        "country": row.country,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    }

@router.post("/", response_model=Unit, status_code=status.HTTP_201_CREATED)
async def create_unit(
    unit: UnitCreate,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new hotel unit"""
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
        INSERT INTO units (id, name, code, description, address, city, country)
        VALUES (:id, :name, :code, :description, :address, :city, :country)
    """), {
        "id": new_id,
        "name": unit.name,
        "code": unit.code,
        "description": unit.description,
        "address": unit.address,
        "city": unit.city,
        "country": unit.country
    })
    db.commit()
    
    # Return the created unit
    return await get_unit(UUID(new_id), db, current_user)
