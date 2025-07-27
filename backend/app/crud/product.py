from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import csv
from decimal import Decimal
from datetime import datetime

from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.crud.base import CRUDBase
from app.models.product import (
    Product, 
    ProductCategory, 
    ProductSupplier, 
    ProductUnitAllocation
)
from app.schemas.product import (
    ProductCreate, 
    ProductUpdate,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductSupplierCreate,
    ProductSupplierUpdate,
    ProductImportResponse
)


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def get_by_sku(self, db: Session, *, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self.get_by_field(db, field="sku", value=sku)

    def get_by_name(self, db: Session, *, name: str) -> Optional[Product]:
        """Get product by name."""
        return self.get_by_field(db, field="name", value=name)

    def get_multi_with_filters(
        self,
        db: Session,
        *,
        unit_ids: Optional[List[UUID]] = None,
        category_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Product], int]:
        """
        Get products with comprehensive filtering for multi-tenant support.
        """
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.unit_allocations),
            joinedload(Product.supplier_relationships)
        )
        
        # Apply soft delete filter
        if hasattr(Product, 'is_deleted'):
            query = query.filter(Product.is_deleted == False)
        
        # Filter by active status
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        # Filter by category
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        # Filter by units (multi-tenant)
        if unit_ids:
            query = query.join(ProductUnitAllocation).filter(
                ProductUnitAllocation.unit_id.in_(unit_ids)
            )
        
        # Filter by supplier
        if supplier_id:
            query = query.join(ProductSupplier).filter(
                ProductSupplier.supplier_id == supplier_id
            )
            if unit_ids:
                query = query.filter(ProductSupplier.unit_id.in_(unit_ids))
        
        # Search functionality
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.description).like(search_term),
                    func.lower(Product.sku).like(search_term)
                )
            )
        
        # Remove duplicates if joined with other tables
        query = query.distinct()
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(Product.name.asc())
        products = query.offset(skip).limit(limit).all()
        
        return products, total

    def create(self, db: Session, *, obj_in: ProductCreate, created_by: UUID) -> Product:
        """
        Create product with unit allocations and supplier relationships.
        """
        # Create base product
        product_data = obj_in.dict(exclude={'unit_allocations', 'supplier_relationships'})
        product_data['created_by'] = created_by
        
        db_product = Product(**product_data)
        db.add(db_product)
        
        try:
            db.flush()  # Get the product ID without committing
            
            # Create unit allocations
            if obj_in.unit_allocations:
                for allocation in obj_in.unit_allocations:
                    db_allocation = ProductUnitAllocation(
                        product_id=db_product.id,
                        unit_id=allocation.unit_id,
                        min_stock_level=allocation.min_stock_level,
                        max_stock_level=allocation.max_stock_level,
                        reorder_point=allocation.reorder_point,
                        current_stock=allocation.current_stock or 0
                    )
                    db.add(db_allocation)
            
            # Create supplier relationships
            if obj_in.supplier_relationships:
                for relationship in obj_in.supplier_relationships:
                    db_relationship = ProductSupplier(
                        product_id=db_product.id,
                        supplier_id=relationship.supplier_id,
                        unit_id=relationship.unit_id,
                        price=relationship.price,
                        is_primary_supplier=relationship.is_primary_supplier,
                        minimum_order_quantity=relationship.minimum_order_quantity,
                        lead_time_days=relationship.lead_time_days
                    )
                    db.add(db_relationship)
            
            db.commit()
            db.refresh(db_product)
            return db_product
            
        except IntegrityError as e:
            db.rollback()
            raise e

    def search_products(
        self,
        db: Session,
        *,
        search_query: str,
        unit_ids: List[UUID],
        limit: int = 20
    ) -> Tuple[List[Product], int]:
        """
        Advanced product search with full-text capabilities.
        """
        # Use PostgreSQL full-text search if available, otherwise use LIKE
        search_term = f"%{search_query.lower()}%"
        
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.unit_allocations)
        )
        
        # Filter by units
        query = query.join(ProductUnitAllocation).filter(
            ProductUnitAllocation.unit_id.in_(unit_ids)
        )
        
        # Apply soft delete and active filters
        if hasattr(Product, 'is_deleted'):
            query = query.filter(Product.is_deleted == False)
        query = query.filter(Product.is_active == True)
        
        # Search across multiple fields
        query = query.filter(
            or_(
                func.lower(Product.name).like(search_term),
                func.lower(Product.description).like(search_term),
                func.lower(Product.sku).like(search_term),
                func.lower(Product.brand).like(search_term)
            )
        )
        
        query = query.distinct()
        total = query.count()
        
        # Order by relevance (name matches first, then description)
        products = query.order_by(
            func.lower(Product.name).like(search_term).desc(),
            Product.name.asc()
        ).limit(limit).all()
        
        return products, total

    def get_products_by_category(
        self, 
        db: Session, 
        *, 
        category_id: UUID,
        unit_ids: Optional[List[UUID]] = None
    ) -> List[Product]:
        """Get all products in a category."""
        query = db.query(Product).filter(Product.category_id == category_id)
        
        if unit_ids:
            query = query.join(ProductUnitAllocation).filter(
                ProductUnitAllocation.unit_id.in_(unit_ids)
            )
        
        if hasattr(Product, 'is_deleted'):
            query = query.filter(Product.is_deleted == False)
        
        return query.distinct().all()

    def get_low_stock_products(
        self, 
        db: Session, 
        *, 
        unit_id: UUID
    ) -> List[Product]:
        """Get products with stock below reorder point."""
        query = db.query(Product).join(ProductUnitAllocation).filter(
            and_(
                ProductUnitAllocation.unit_id == unit_id,
                ProductUnitAllocation.current_stock <= ProductUnitAllocation.reorder_point
            )
        )
        
        if hasattr(Product, 'is_deleted'):
            query = query.filter(Product.is_deleted == False)
        
        return query.filter(Product.is_active == True).all()

    def update_stock_level(
        self,
        db: Session,
        *,
        product_id: UUID,
        unit_id: UUID,
        new_stock_level: int,
        updated_by: UUID
    ) -> Optional[ProductUnitAllocation]:
        """Update stock level for a product in a specific unit."""
        allocation = db.query(ProductUnitAllocation).filter(
            and_(
                ProductUnitAllocation.product_id == product_id,
                ProductUnitAllocation.unit_id == unit_id
            )
        ).first()
        
        if allocation:
            allocation.current_stock = new_stock_level
            allocation.last_updated = datetime.utcnow()
            allocation.updated_by = updated_by
            
            try:
                db.commit()
                db.refresh(allocation)
                return allocation
            except IntegrityError as e:
                db.rollback()
                raise e
        
        return None

    def import_products_from_csv(
        self,
        db: Session,
        *,
        csv_reader,
        unit_id: UUID,
        created_by: UUID,
        update_existing: bool = False
    ) -> ProductImportResponse:
        """
        Import products from CSV file.
        Expected columns: name, description, category, sku, unit_of_measure, supplier_code, price
        """
        imported_count = 0
        updated_count = 0
        errors = []
        
        try:
            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
                try:
                    # Validate required fields
                    required_fields = ['name', 'sku']
                    for field in required_fields:
                        if not row.get(field, '').strip():
                            errors.append(f"Row {row_num}: Missing required field '{field}'")
                            continue
                    
                    if errors and len(errors) > 100:  # Limit errors to prevent memory issues
                        break
                    
                    # Check if product exists
                    existing_product = self.get_by_sku(db, sku=row['sku'].strip())
                    
                    if existing_product and not update_existing:
                        errors.append(f"Row {row_num}: Product with SKU '{row['sku']}' already exists")
                        continue
                    
                    # Get or create category
                    category_id = None
                    if row.get('category', '').strip():
                        category = self.get_category_by_name(db, name=row['category'].strip())
                        if not category:
                            # Create new category
                            category = self.create_category(db, obj_in={
                                'name': row['category'].strip(),
                                'description': f"Auto-created from import"
                            })
                        category_id = category.id
                    
                    # Prepare product data
                    product_data = {
                        'name': row['name'].strip(),
                        'description': row.get('description', '').strip(),
                        'sku': row['sku'].strip(),
                        'category_id': category_id,
                        'unit_of_measure': row.get('unit_of_measure', 'each').strip(),
                        'brand': row.get('brand', '').strip(),
                        'is_active': True
                    }
                    
                    if existing_product and update_existing:
                        # Update existing product
                        for field, value in product_data.items():
                            if value:  # Only update non-empty values
                                setattr(existing_product, field, value)
                        
                        db.add(existing_product)
                        updated_count += 1
                        product = existing_product
                    else:
                        # Create new product
                        product = Product(**product_data, created_by=created_by)
                        db.add(product)
                        db.flush()  # Get ID
                        imported_count += 1
                    
                    # Create or update unit allocation
                    allocation = db.query(ProductUnitAllocation).filter(
                        and_(
                            ProductUnitAllocation.product_id == product.id,
                            ProductUnitAllocation.unit_id == unit_id
                        )
                    ).first()
                    
                    if not allocation:
                        allocation = ProductUnitAllocation(
                            product_id=product.id,
                            unit_id=unit_id,
                            current_stock=int(row.get('current_stock', 0) or 0),
                            min_stock_level=int(row.get('min_stock', 0) or 0),
                            max_stock_level=int(row.get('max_stock', 100) or 100),
                            reorder_point=int(row.get('reorder_point', 10) or 10)
                        )
                        db.add(allocation)
                    
                    # Create supplier relationship if supplier info provided
                    if row.get('supplier_code', '').strip() and row.get('price', '').strip():
                        # This would need a supplier lookup - simplified for now
                        try:
                            price = Decimal(str(row['price']))
                            # Add supplier relationship logic here
                        except (ValueError, TypeError):
                            errors.append(f"Row {row_num}: Invalid price format")
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue
            
            # Commit all changes
            db.commit()
            
            return ProductImportResponse(
                total_imported=imported_count,
                total_updated=updated_count,
                total_errors=len(errors),
                errors=errors[:50]  # Limit errors returned
            )
            
        except Exception as e:
            db.rollback()
            raise e

    # Product Category operations
    def get_categories(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ProductCategory]:
        """Get all product categories."""
        return db.query(ProductCategory).filter(
            ProductCategory.is_active == True
        ).order_by(ProductCategory.name.asc()).offset(skip).limit(limit).all()

    def get_category(self, db: Session, *, id: UUID) -> Optional[ProductCategory]:
        """Get category by ID."""
        return db.query(ProductCategory).filter(ProductCategory.id == id).first()

    def get_category_by_name(self, db: Session, *, name: str) -> Optional[ProductCategory]:
        """Get category by name."""
        return db.query(ProductCategory).filter(
            func.lower(ProductCategory.name) == name.lower()
        ).first()

    def create_category(
        self, 
        db: Session, 
        *, 
        obj_in: ProductCategoryCreate
    ) -> ProductCategory:
        """Create new product category."""
        db_obj = ProductCategory(**obj_in.dict())
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_category(
        self,
        db: Session,
        *,
        db_obj: ProductCategory,
        obj_in: ProductCategoryUpdate
    ) -> ProductCategory:
        """Update product category."""
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def remove_category(self, db: Session, *, id: UUID) -> Optional[ProductCategory]:
        """Delete product category."""
        category = db.query(ProductCategory).get(id)
        if category:
            db.delete(category)
            
            try:
                db.commit()
                return category
            except IntegrityError as e:
                db.rollback()
                raise e
        return None

    # Product-Supplier relationship operations
    def get_product_suppliers(
        self,
        db: Session,
        *,
        product_id: UUID,
        unit_ids: Optional[List[UUID]] = None
    ) -> List[ProductSupplier]:
        """Get suppliers for a product."""
        query = db.query(ProductSupplier).filter(
            ProductSupplier.product_id == product_id
        )
        
        if unit_ids:
            query = query.filter(ProductSupplier.unit_id.in_(unit_ids))
        
        return query.all()

    def get_product_supplier(self, db: Session, *, id: UUID) -> Optional[ProductSupplier]:
        """Get product-supplier relationship by ID."""
        return db.query(ProductSupplier).filter(ProductSupplier.id == id).first()

    def get_product_supplier_relationship(
        self,
        db: Session,
        *,
        product_id: UUID,
        supplier_id: UUID,
        unit_id: UUID
    ) -> Optional[ProductSupplier]:
        """Get specific product-supplier-unit relationship."""
        return db.query(ProductSupplier).filter(
            and_(
                ProductSupplier.product_id == product_id,
                ProductSupplier.supplier_id == supplier_id,
                ProductSupplier.unit_id == unit_id
            )
        ).first()

    def create_product_supplier(
        self,
        db: Session,
        *,
        obj_in: ProductSupplierCreate,
        product_id: UUID
    ) -> ProductSupplier:
        """Create product-supplier relationship."""
        db_obj = ProductSupplier(
            product_id=product_id,
            **obj_in.dict()
        )
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_product_supplier(
        self,
        db: Session,
        *,
        db_obj: ProductSupplier,
        obj_in: ProductSupplierUpdate
    ) -> ProductSupplier:
        """Update product-supplier relationship."""
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def remove_product_supplier(self, db: Session, *, id: UUID) -> Optional[ProductSupplier]:
        """Remove product-supplier relationship."""
        relationship = db.query(ProductSupplier).get(id)
        if relationship:
            db.delete(relationship)
            
            try:
                db.commit()
                return relationship
            except IntegrityError as e:
                db.rollback()
                raise e
        return None

    def get_primary_supplier(
        self,
        db: Session,
        *,
        product_id: UUID,
        unit_id: UUID
    ) -> Optional[ProductSupplier]:
        """Get primary supplier for a product in a specific unit."""
        return db.query(ProductSupplier).filter(
            and_(
                ProductSupplier.product_id == product_id,
                ProductSupplier.unit_id == unit_id,
                ProductSupplier.is_primary_supplier == True
            )
        ).first()

    def get_products_by_supplier(
        self,
        db: Session,
        *,
        supplier_id: UUID,
        unit_id: Optional[UUID] = None
    ) -> List[Product]:
        """Get all products supplied by a supplier."""
        query = db.query(Product).join(ProductSupplier).filter(
            ProductSupplier.supplier_id == supplier_id
        )
        
        if unit_id:
            query = query.filter(ProductSupplier.unit_id == unit_id)
        
        if hasattr(Product, 'is_deleted'):
            query = query.filter(Product.is_deleted == False)
        
        return query.filter(Product.is_active == True).distinct().all()


# Create the CRUD instance
crud_product = CRUDProduct(Product)