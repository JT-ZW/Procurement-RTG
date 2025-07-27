from typing import Any, List, Optional
from uuid import UUID
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_product, crud_unit, crud_supplier
from app.models.user import User
from app.models.product import Product
from app.schemas.product import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse, 
    ProductListResponse,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCategoryResponse,
    ProductSupplierCreate,
    ProductSupplierUpdate,
    ProductSupplierResponse,
    ProductImportResponse,
    ProductSearchParams
)
from app.utils.multi_tenant import check_unit_access, get_user_units

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
def read_products(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    unit_id: Optional[UUID] = Query(None, description="Filter by unit ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
) -> Any:
    """
    Retrieve products with filtering and pagination.
    """
    # Check unit access if unit_id is specified
    if unit_id:
        check_unit_access(db, user=current_user, unit_id=unit_id)
        user_units = [unit_id]
    else:
        user_units = get_user_units(db, user_id=current_user.id)
        if not user_units:
            return {"items": [], "total": 0}
    
    products, total = crud_product.get_multi_with_filters(
        db,
        unit_ids=user_units,
        category_id=category_id,
        supplier_id=supplier_id,
        search=search,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    
    return {"items": products, "total": total}


@router.post("/", response_model=ProductResponse)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new product.
    """
    # Verify user has access to all specified units
    for unit_allocation in product_in.unit_allocations:
        check_unit_access(db, user=current_user, unit_id=unit_allocation.unit_id)
    
    # Verify category exists if specified
    if product_in.category_id:
        category = crud_product.get_category(db, id=product_in.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product category not found"
            )
    
    product = crud_product.create(db, obj_in=product_in, created_by=current_user.id)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get product by ID.
    """
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user has access to at least one unit where this product is allocated
    user_units = get_user_units(db, user_id=current_user.id)
    product_units = [allocation.unit_id for allocation in product.unit_allocations]
    
    if not any(unit_id in user_units for unit_id in product_units):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this product"
        )
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_in: ProductUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update product.
    """
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check access to current product units
    user_units = get_user_units(db, user_id=current_user.id)
    product_units = [allocation.unit_id for allocation in product.unit_allocations]
    
    if not any(unit_id in user_units for unit_id in product_units):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this product"
        )
    
    # If updating unit allocations, verify access to new units
    if product_in.unit_allocations:
        for unit_allocation in product_in.unit_allocations:
            check_unit_access(db, user=current_user, unit_id=unit_allocation.unit_id)
    
    product = crud_product.update(db, db_obj=product, obj_in=product_in)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete product (soft delete).
    """
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check access
    user_units = get_user_units(db, user_id=current_user.id)
    product_units = [allocation.unit_id for allocation in product.unit_allocations]
    
    if not any(unit_id in user_units for unit_id in product_units):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this product"
        )
    
    crud_product.remove(db, id=product_id)
    return {"message": "Product deleted successfully"}


# Product Categories
@router.get("/categories/", response_model=List[ProductCategoryResponse])
def read_product_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
) -> Any:
    """
    Retrieve product categories.
    """
    categories = crud_product.get_categories(db, skip=skip, limit=limit)
    return categories


@router.post("/categories/", response_model=ProductCategoryResponse)
def create_product_category(
    category_in: ProductCategoryCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new product category.
    """
    # Check if category with same name exists
    existing = crud_product.get_category_by_name(db, name=category_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    category = crud_product.create_category(db, obj_in=category_in)
    return category


@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
def update_product_category(
    category_id: UUID,
    category_in: ProductCategoryUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update product category.
    """
    category = crud_product.get_category(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category = crud_product.update_category(db, db_obj=category, obj_in=category_in)
    return category


@router.delete("/categories/{category_id}")
def delete_product_category(
    category_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete product category.
    """
    category = crud_product.get_category(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category is being used by any products
    products_using_category = crud_product.get_products_by_category(db, category_id=category_id)
    if products_using_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category that is being used by products"
        )
    
    crud_product.remove_category(db, id=category_id)
    return {"message": "Category deleted successfully"}


# Product-Supplier Relationships
@router.get("/{product_id}/suppliers", response_model=List[ProductSupplierResponse])
def read_product_suppliers(
    product_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    unit_id: Optional[UUID] = Query(None, description="Filter by unit")
) -> Any:
    """
    Get suppliers for a specific product.
    """
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check access
    user_units = get_user_units(db, user_id=current_user.id)
    if unit_id:
        check_unit_access(db, user=current_user, unit_id=unit_id)
        filter_units = [unit_id]
    else:
        filter_units = user_units
    
    suppliers = crud_product.get_product_suppliers(
        db, 
        product_id=product_id, 
        unit_ids=filter_units
    )
    return suppliers


@router.post("/{product_id}/suppliers", response_model=ProductSupplierResponse)
def create_product_supplier(
    product_id: UUID,
    supplier_in: ProductSupplierCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Add supplier to product for specific unit.
    """
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check unit access
    check_unit_access(db, user=current_user, unit_id=supplier_in.unit_id)
    
    # Verify supplier exists
    supplier = crud_supplier.get(db, id=supplier_in.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Check if relationship already exists
    existing = crud_product.get_product_supplier_relationship(
        db,
        product_id=product_id,
        supplier_id=supplier_in.supplier_id,
        unit_id=supplier_in.unit_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product-supplier relationship already exists for this unit"
        )
    
    relationship = crud_product.create_product_supplier(
        db, 
        obj_in=supplier_in, 
        product_id=product_id
    )
    return relationship


@router.put("/suppliers/{relationship_id}", response_model=ProductSupplierResponse)
def update_product_supplier(
    relationship_id: UUID,
    supplier_in: ProductSupplierUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update product-supplier relationship.
    """
    relationship = crud_product.get_product_supplier(db, id=relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product-supplier relationship not found"
        )
    
    # Check unit access
    check_unit_access(db, user=current_user, unit_id=relationship.unit_id)
    
    relationship = crud_product.update_product_supplier(
        db, 
        db_obj=relationship, 
        obj_in=supplier_in
    )
    return relationship


@router.delete("/suppliers/{relationship_id}")
def delete_product_supplier(
    relationship_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Remove supplier from product.
    """
    relationship = crud_product.get_product_supplier(db, id=relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product-supplier relationship not found"
        )
    
    # Check unit access
    check_unit_access(db, user=current_user, unit_id=relationship.unit_id)
    
    crud_product.remove_product_supplier(db, id=relationship_id)
    return {"message": "Product-supplier relationship removed successfully"}


# Bulk Operations
@router.post("/import", response_model=ProductImportResponse)
async def import_products(
    file: UploadFile = File(...),
    unit_id: UUID = Form(...),
    update_existing: bool = Form(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Import products from CSV file.
    Expected CSV columns: name, description, category, sku, unit_of_measure, supplier_code, price
    """
    # Check unit access
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    try:
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        results = crud_product.import_products_from_csv(
            db,
            csv_reader=csv_reader,
            unit_id=unit_id,
            created_by=current_user.id,
            update_existing=update_existing
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV file: {str(e)}"
        )


@router.get("/export/csv")
def export_products_csv(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    unit_id: Optional[UUID] = Query(None, description="Filter by unit ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category")
) -> Any:
    """
    Export products to CSV file.
    """
    # Get user units
    if unit_id:
        check_unit_access(db, user=current_user, unit_id=unit_id)
        user_units = [unit_id]
    else:
        user_units = get_user_units(db, user_id=current_user.id)
    
    if not user_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No accessible units found"
        )
    
    # Get products
    products, _ = crud_product.get_multi_with_filters(
        db,
        unit_ids=user_units,
        category_id=category_id,
        skip=0,
        limit=10000  # Large limit for export
    )
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Product Name', 'Description', 'SKU', 'Category', 'Unit of Measure',
        'Unit', 'Supplier', 'Price', 'Is Active', 'Created Date'
    ])
    
    # Write data
    for product in products:
        for allocation in product.unit_allocations:
            for supplier_rel in product.supplier_relationships:
                if supplier_rel.unit_id == allocation.unit_id:
                    writer.writerow([
                        product.name,
                        product.description,
                        product.sku,
                        product.category.name if product.category else '',
                        product.unit_of_measure,
                        allocation.unit.name if allocation.unit else '',
                        supplier_rel.supplier.company_name if supplier_rel.supplier else '',
                        supplier_rel.price,
                        product.is_active,
                        product.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_export.csv"}
    )


@router.get("/search", response_model=ProductListResponse)
def search_products(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    q: str = Query(..., min_length=2, description="Search query"),
    unit_id: Optional[UUID] = Query(None, description="Filter by unit ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return")
) -> Any:
    """
    Advanced product search with full-text capabilities.
    """
    # Check unit access if unit_id is specified
    if unit_id:
        check_unit_access(db, user=current_user, unit_id=unit_id)
        user_units = [unit_id]
    else:
        user_units = get_user_units(db, user_id=current_user.id)
    
    if not user_units:
        return {"items": [], "total": 0}
    
    products, total = crud_product.search_products(
        db,
        search_query=q,
        unit_ids=user_units,
        limit=limit
    )
    
    return {"items": products, "total": total}