"""
Products API endpoints for the Hotel Procurement System - Enhanced E-catalogue
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.product import (
    Product, ProductCreate, ProductUpdate, ECatalogueProduct,
    ProductCategory, ProductCategoryCreate, ProductCategoryUpdate,
    StockUpdate, ConsumptionRateUpdate
)

router = APIRouter()

@router.get("/", response_model=List[ECatalogueProduct])
async def get_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    unit_id: Optional[str] = Query(None, description="Filter by unit ID"),
    stock_status: Optional[str] = Query(None, description="Filter by stock status"),
    search: Optional[str] = Query(None, description="Search in name, code, or description"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products with E-catalogue information"""
    from sqlalchemy import text
    
    # Use the exact same pattern as the working e-catalogue endpoint
    query = "SELECT * FROM e_catalogue_view WHERE is_active = true"
    params = {"limit": limit, "skip": skip}
    conditions = []
    
    if category_id:
        conditions.append("category_id = :category_id")
        params["category_id"] = category_id
    
    if supplier_id:
        conditions.append("supplier_id = :supplier_id")
        params["supplier_id"] = supplier_id
    
    if unit_id:
        conditions.append("unit_id = :unit_id")
        params["unit_id"] = unit_id
        
    if stock_status:
        conditions.append("stock_status = :stock_status")
        params["stock_status"] = stock_status
    
    if search:
        conditions.append("(name ILIKE :search OR code ILIKE :search OR description ILIKE :search)")
        params["search"] = f"%{search}%"
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += " ORDER BY name LIMIT :limit OFFSET :skip"
    
    result = await db.execute(text(query), params)
    
    products = []
    for row in result:
        products.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "description": row.description,
            "category_name": row.category_name,
            "unit_of_measure": row.unit_of_measure,
            "effective_unit_price": float(row.effective_unit_price) if row.effective_unit_price else None,
            "contract_price": float(row.contract_price) if row.contract_price else None,
            "standard_cost": float(row.standard_cost) if row.standard_cost else None,
            "currency": row.currency,
            "current_stock_quantity": float(row.current_stock_quantity) if row.current_stock_quantity else 0,
            "minimum_stock_level": row.minimum_stock_level,
            "maximum_stock_level": row.maximum_stock_level,
            "reorder_point": row.reorder_point,
            "estimated_consumption_rate_per_day": float(row.estimated_consumption_rate_per_day) if row.estimated_consumption_rate_per_day else 0,
            "estimated_days_stock_will_last": float(row.estimated_days_stock_will_last) if row.estimated_days_stock_will_last else None,
            "stock_status": row.stock_status,
            "supplier_name": row.supplier_name,
            "unit_name": row.unit_name,
            "specifications": row.specifications,
            "is_active": row.is_active,
            "last_restocked_date": row.last_restocked_date.isoformat() if row.last_restocked_date else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return products

@router.get("/e-catalogue/", response_model=List[ECatalogueProduct])
async def get_e_catalogue(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[str] = Query(None),
    supplier_id: Optional[str] = Query(None),
    unit_id: Optional[str] = Query(None),
    stock_status: Optional[str] = Query(None, regex="^(LOW_STOCK|REORDER_NEEDED|OVERSTOCK|NORMAL)$"),
    low_stock_only: bool = Query(False, description="Show only products with low stock"),
    search: Optional[str] = Query(None),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get E-catalogue view with all required fields and calculations"""
    from sqlalchemy import text
    
    query = """
        SELECT * FROM e_catalogue_view
        WHERE is_active = true
    """
    
    params = {"limit": limit, "skip": skip}
    conditions = []
    
    if category_id:
        conditions.append("category_id = :category_id")
        params["category_id"] = category_id
    
    if supplier_id:
        conditions.append("supplier_id = :supplier_id")
        params["supplier_id"] = supplier_id
    
    if unit_id:
        conditions.append("unit_id = :unit_id")
        params["unit_id"] = unit_id
        
    if stock_status:
        conditions.append("stock_status = :stock_status")
        params["stock_status"] = stock_status
    
    if low_stock_only:
        conditions.append("stock_status IN ('LOW_STOCK', 'REORDER_NEEDED')")
        
    if search:
        conditions.append("(name ILIKE :search OR code ILIKE :search OR description ILIKE :search)")
        params["search"] = f"%{search}%"
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += " ORDER BY name LIMIT :limit OFFSET :skip"
    
    result = await db.execute(text(query), params)
    
    catalogue = []
    for row in result:
        catalogue.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "description": row.description,
            "category_name": row.category_name,
            "unit_of_measure": row.unit_of_measure,
            "effective_unit_price": float(row.effective_unit_price) if row.effective_unit_price else None,
            "contract_price": float(row.contract_price) if row.contract_price else None,
            "standard_cost": float(row.standard_cost) if row.standard_cost else None,
            "currency": row.currency,
            "current_stock_quantity": float(row.current_stock_quantity),
            "minimum_stock_level": row.minimum_stock_level,
            "maximum_stock_level": row.maximum_stock_level,
            "reorder_point": row.reorder_point,
            "estimated_consumption_rate_per_day": float(row.estimated_consumption_rate_per_day),
            "estimated_days_stock_will_last": float(row.estimated_days_stock_will_last) if row.estimated_days_stock_will_last else None,
            "stock_status": row.stock_status,
            "supplier_name": row.supplier_name,
            "unit_name": row.unit_name,
            "specifications": row.specifications,
            "is_active": row.is_active,
            "last_restocked_date": row.last_restocked_date.isoformat() if row.last_restocked_date else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return catalogue

@router.get("/categories/", response_model=List[ProductCategory])
async def get_product_categories(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all product categories"""
    from sqlalchemy import text
    
    result = await db.execute(text("""
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

@router.post("/categories/", response_model=ProductCategory, status_code=status.HTTP_201_CREATED)
async def create_product_category(
    category: ProductCategoryCreate,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product category"""
    if current_user.role not in ['manager', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    import uuid
    
    new_id = str(uuid.uuid4())
    
    await db.execute(text("""
        INSERT INTO product_categories (id, name, code, description, parent_category_id, is_active)
        VALUES (:id, :name, :code, :description, :parent_category_id, :is_active)
    """), {
        "id": new_id,
        "name": category.name,
        "code": category.code,
        "description": category.description,
        "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
        "is_active": category.is_active
    })
    await db.commit()
    
    # Return the created category
    result = await db.execute(text("""
        SELECT id, name, code, description, parent_category_id, is_active, created_at, updated_at
        FROM product_categories WHERE id = :id
    """), {"id": new_id})
    
    row = result.first()
    return {
        "id": str(row.id),
        "name": row.name,
        "code": row.code,
        "description": row.description,
        "parent_category_id": str(row.parent_category_id) if row.parent_category_id else None,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    }

@router.get("/{product_id}", response_model=ECatalogueProduct)
async def get_product(
    product_id: UUID,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific product by ID with all E-catalogue information"""
    from sqlalchemy import text
    
    # Use the same e_catalogue_view pattern that works for other endpoints
    result = await db.execute(text("""
        SELECT * FROM e_catalogue_view
        WHERE id = :product_id AND is_active = true
    """), {"product_id": str(product_id)})
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Use the same mapping pattern as other endpoints
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
        "contract_price": float(row.contract_price) if row.contract_price else None,
        "effective_unit_price": float(row.effective_unit_price) if row.effective_unit_price else None,
        "currency": row.currency,
        "current_stock_quantity": float(row.current_stock_quantity) if row.current_stock_quantity else 0,
        "minimum_stock_level": row.minimum_stock_level,
        "maximum_stock_level": row.maximum_stock_level,
        "reorder_point": row.reorder_point,
        "estimated_consumption_rate_per_day": float(row.estimated_consumption_rate_per_day) if row.estimated_consumption_rate_per_day else 0,
        "estimated_days_stock_will_last": float(row.estimated_days_stock_will_last) if row.estimated_days_stock_will_last else None,
        "stock_status": row.stock_status,
        "supplier_id": str(row.supplier_id) if row.supplier_id else None,
        "supplier_name": row.supplier_name,
        "supplier_code": row.supplier_code,
        "unit_id": str(row.unit_id) if row.unit_id else None,
        "unit_name": row.unit_name,
        "unit_code": row.unit_code,
        "specifications": row.specifications,
        "is_active": row.is_active,
        "last_restocked_date": row.last_restocked_date.isoformat() if row.last_restocked_date else None,
        "last_consumption_update": row.last_consumption_update.isoformat() if row.last_consumption_update else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    }

@router.post("/", response_model=ECatalogueProduct, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product with all E-catalogue fields"""
    # Check if user has permission (only managers and superusers)
    if current_user.role not in ['manager', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    import uuid
    
    new_id = str(uuid.uuid4())
    
    # Validate that all mandatory E-catalogue fields are provided
    if not all([
        product.name, product.code, product.unit_of_measure,
        product.minimum_stock_level is not None,
        product.maximum_stock_level is not None, 
        product.estimated_consumption_rate_per_day is not None
    ]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="All E-catalogue mandatory fields must be provided: name, code, unit_of_measure, minimum_stock_level, maximum_stock_level, estimated_consumption_rate_per_day"
        )
    
    await db.execute(text("""
        INSERT INTO products (
            id, name, code, description, category_id, unit_of_measure,
            standard_cost, contract_price, currency, 
            current_stock_quantity, minimum_stock_level, maximum_stock_level,
            reorder_point, estimated_consumption_rate_per_day,
            supplier_id, unit_id, specifications, is_active
        )
        VALUES (
            :id, :name, :code, :description, :category_id, :unit_of_measure,
            :standard_cost, :contract_price, :currency,
            :current_stock_quantity, :minimum_stock_level, :maximum_stock_level,
            :reorder_point, :estimated_consumption_rate_per_day,
            :supplier_id, :unit_id, :specifications, :is_active
        )
    """), {
        "id": new_id,
        "name": product.name,
        "code": product.code,
        "description": product.description,
        "category_id": str(product.category_id) if product.category_id else None,
        "unit_of_measure": product.unit_of_measure,
        "standard_cost": product.standard_cost,
        "contract_price": product.contract_price,
        "currency": product.currency,
        "current_stock_quantity": product.current_stock_quantity,
        "minimum_stock_level": product.minimum_stock_level,
        "maximum_stock_level": product.maximum_stock_level,
        "reorder_point": product.reorder_point,
        "estimated_consumption_rate_per_day": product.estimated_consumption_rate_per_day,
        "supplier_id": str(product.supplier_id) if product.supplier_id else None,
        "unit_id": str(product.unit_id) if product.unit_id else None,
        "specifications": product.specifications,
        "is_active": product.is_active
    })
    await db.commit()
    
    # Return the created product
    return await get_product(UUID(new_id), db, current_user)

@router.put("/{product_id}", response_model=ECatalogueProduct)
async def update_product(
    product_id: UUID,
    product: ProductUpdate,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    if current_user.role not in ['manager', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    
    # Check if product exists
    check_result = await db.execute(text("SELECT id FROM products WHERE id = :product_id"), 
                             {"product_id": str(product_id)})
    if not check_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Build update query dynamically
    update_fields = []
    params = {"product_id": str(product_id)}
    
    for field, value in product.dict(exclude_unset=True).items():
        if field in ['category_id', 'supplier_id', 'unit_id'] and value:
            update_fields.append(f"{field} = :{field}")
            params[field] = str(value)
        elif field == 'specifications':
            update_fields.append(f"{field} = :{field}")
            params[field] = value
        elif value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = :product_id"
        await db.execute(text(query), params)
        await db.commit()
    
    return await get_product(product_id, db, current_user)

@router.patch("/{product_id}/stock", response_model=ECatalogueProduct)
async def update_product_stock(
    product_id: UUID,
    stock_update: StockUpdate,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product stock levels"""
    if current_user.role not in ['manager', 'superuser', 'store_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    
    # Check if product exists
    check_result = await db.execute(text("SELECT id FROM products WHERE id = :product_id"), 
                             {"product_id": str(product_id)})
    if not check_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    restock_date = stock_update.last_restocked_date or datetime.now()
    
    await db.execute(text("""
        UPDATE products 
        SET current_stock_quantity = :quantity,
            last_restocked_date = :restock_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :product_id
    """), {
        "product_id": str(product_id),
        "quantity": stock_update.current_stock_quantity,
        "restock_date": restock_date
    })
    await db.commit()
    
    return await get_product(product_id, db, current_user)

@router.patch("/{product_id}/consumption", response_model=ECatalogueProduct)
async def update_consumption_rate(
    product_id: UUID,
    consumption_update: ConsumptionRateUpdate,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product consumption rate"""
    if current_user.role not in ['manager', 'superuser', 'store_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    
    # Check if product exists
    check_result = await db.execute(text("SELECT id FROM products WHERE id = :product_id"), 
                             {"product_id": str(product_id)})
    if not check_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_date = consumption_update.last_consumption_update or datetime.now()
    
    await db.execute(text("""
        UPDATE products 
        SET estimated_consumption_rate_per_day = :rate,
            last_consumption_update = :update_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :product_id
    """), {
        "product_id": str(product_id),
        "rate": consumption_update.estimated_consumption_rate_per_day,
        "update_date": update_date
    })
    await db.commit()
    
    return await get_product(product_id, db, current_user)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a product (set is_active to false)"""
    if current_user.role not in ['manager', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import text
    
    # Check if product exists
    check_result = await db.execute(text("SELECT id FROM products WHERE id = :product_id AND is_active = true"), 
                             {"product_id": str(product_id)})
    if not check_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    await db.execute(text("""
        UPDATE products 
        SET is_active = false, updated_at = CURRENT_TIMESTAMP
        WHERE id = :product_id
    """), {"product_id": str(product_id)})
    await db.commit()
    
    return None
