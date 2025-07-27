"""
Products API endpoints for the Hotel Procurement System
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.product import Product, ProductCreate, ProductUpdate

router = APIRouter()

@router.get("/", response_model=List[Product])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products"""
    from sqlalchemy import text
    
    base_query = """
        SELECT p.id, p.name, p.code, p.description, p.category_id, p.unit_of_measure,
               p.standard_cost, p.currency, p.minimum_stock_level, p.maximum_stock_level,
               p.reorder_point, p.is_active, p.created_at, p.updated_at,
               pc.name as category_name, pc.code as category_code
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.is_active = true
    """
    
    params = {"limit": limit, "skip": skip}
    
    if category_id:
        base_query += " AND p.category_id = :category_id"
        params["category_id"] = category_id
    
    base_query += " ORDER BY p.name LIMIT :limit OFFSET :skip"
    
    result = db.execute(text(base_query), params)
    
    products = []
    for row in result:
        products.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "description": row.description,
            "category_id": str(row.category_id) if row.category_id else None,
            "category_name": row.category_name,
            "category_code": row.category_code,
            "unit_of_measure": row.unit_of_measure,
            "standard_cost": float(row.standard_cost) if row.standard_cost else None,
            "currency": row.currency,
            "minimum_stock_level": row.minimum_stock_level,
            "maximum_stock_level": row.maximum_stock_level,
            "reorder_point": row.reorder_point,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return products

@router.get("/categories/", response_model=List[dict])
async def get_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all product categories"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, name, code, description, parent_category_id, is_active,
               created_at, updated_at
        FROM product_categories 
        WHERE is_active = true
        ORDER BY name
    """))
    
    categories = []
    for row in result:
        categories.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "description": row.description,
            "parent_category_id": str(row.parent_category_id) if row.parent_category_id else None,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return categories

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific product by ID"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT p.id, p.name, p.code, p.description, p.category_id, p.unit_of_measure,
               p.standard_cost, p.currency, p.minimum_stock_level, p.maximum_stock_level,
               p.reorder_point, p.is_active, p.created_at, p.updated_at,
               pc.name as category_name, pc.code as category_code
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.id = :product_id
    """), {"product_id": str(product_id)})
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {
        "id": str(row.id),
        "name": row.name,
        "code": row.code,
        "description": row.description,
        "category_id": str(row.category_id) if row.category_id else None,
        "category_name": row.category_name,
        "category_code": row.category_code,
        "unit_of_measure": row.unit_of_measure,
        "standard_cost": float(row.standard_cost) if row.standard_cost else None,
        "currency": row.currency,
        "minimum_stock_level": row.minimum_stock_level,
        "maximum_stock_level": row.maximum_stock_level,
        "reorder_point": row.reorder_point,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    }

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product"""
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
        INSERT INTO products (id, name, code, description, category_id, unit_of_measure,
                            standard_cost, currency, minimum_stock_level, maximum_stock_level,
                            reorder_point)
        VALUES (:id, :name, :code, :description, :category_id, :unit_of_measure,
                :standard_cost, :currency, :minimum_stock_level, :maximum_stock_level,
                :reorder_point)
    """), {
        "id": new_id,
        "name": product.name,
        "code": product.code,
        "description": product.description,
        "category_id": str(product.category_id) if product.category_id else None,
        "unit_of_measure": product.unit_of_measure,
        "standard_cost": product.standard_cost,
        "currency": product.currency,
        "minimum_stock_level": product.minimum_stock_level,
        "maximum_stock_level": product.maximum_stock_level,
        "reorder_point": product.reorder_point
    })
    db.commit()
    
    # Return the created product
    return await get_product(UUID(new_id), db, current_user)
