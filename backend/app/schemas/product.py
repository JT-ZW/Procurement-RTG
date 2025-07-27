"""
Pydantic schemas for product management.
Handles products, categories, supplier relationships, and inventory operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


# Product Category Schemas

class ProductCategoryBase(BaseModel):
    """Base schema for product categories."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    display_order: int = Field(0, ge=0)
    is_active: bool = True
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()


class ProductCategoryCreate(ProductCategoryBase):
    """Schema for creating product categories."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Food & Beverage",
                "description": "All food and beverage items",
                "parent_id": None,
                "display_order": 1,
                "is_active": True
            }
        }


class ProductCategoryUpdate(BaseModel):
    """Schema for updating product categories."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip() if v else v


class ProductCategoryResponse(ProductCategoryBase):
    """Schema for product category responses."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relationships
    subcategories: Optional[List["ProductCategoryResponse"]] = []
    product_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Product Unit Allocation Schemas

class ProductUnitAllocationBase(BaseModel):
    """Base schema for product unit allocations."""
    unit_id: UUID
    current_stock: int = Field(0, ge=0)
    min_stock_level: int = Field(0, ge=0)
    max_stock_level: int = Field(100, ge=1)
    reorder_point: int = Field(10, ge=0)
    reorder_quantity: int = Field(50, ge=1)
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_location: Optional[str] = Field(None, max_length=50)
    is_authorized: bool = True
    requires_unit_approval: bool = False
    budget_category: Optional[str] = Field(None, max_length=50)
    
    @validator('max_stock_level')
    def max_stock_must_be_greater_than_min(cls, v, values):
        if 'min_stock_level' in values and v < values['min_stock_level']:
            raise ValueError('Maximum stock level must be greater than or equal to minimum stock level')
        return v
    
    @validator('reorder_point')
    def reorder_point_validation(cls, v, values):
        if 'min_stock_level' in values and v < values['min_stock_level']:
            raise ValueError('Reorder point should be greater than or equal to minimum stock level')
        return v


class ProductUnitAllocationCreate(ProductUnitAllocationBase):
    """Schema for creating product unit allocations."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "unit_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_stock": 25,
                "min_stock_level": 10,
                "max_stock_level": 100,
                "reorder_point": 15,
                "reorder_quantity": 50,
                "storage_location": "Kitchen Store Room",
                "budget_category": "F&B"
            }
        }


class ProductUnitAllocationUpdate(BaseModel):
    """Schema for updating product unit allocations."""
    current_stock: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=1)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=1)
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_location: Optional[str] = Field(None, max_length=50)
    is_authorized: Optional[bool] = None
    requires_unit_approval: Optional[bool] = None
    budget_category: Optional[str] = Field(None, max_length=50)


class ProductUnitAllocationResponse(ProductUnitAllocationBase):
    """Schema for product unit allocation responses."""
    id: UUID
    product_id: UUID
    last_counted_at: Optional[datetime] = None
    last_counted_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Calculated fields
    needs_reorder: Optional[bool] = None
    stock_status: Optional[str] = None  # "normal", "low_stock", "out_of_stock", "overstock"
    
    # Related objects (when needed)
    unit: Optional["UnitBasic"] = None
    
    class Config:
        from_attributes = True


# Product Supplier Relationship Schemas

class ProductSupplierBase(BaseModel):
    """Base schema for product supplier relationships."""
    supplier_id: UUID
    unit_id: UUID
    is_primary_supplier: bool = False
    priority_order: int = Field(1, ge=1)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field("USD", max_length=3)
    minimum_order_quantity: int = Field(1, ge=1)
    maximum_order_quantity: Optional[int] = Field(None, ge=1)
    order_multiple: int = Field(1, ge=1)
    lead_time_days: int = Field(7, ge=0)
    contract_reference: Optional[str] = Field(None, max_length=100)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_preferred: bool = False
    
    @validator('maximum_order_quantity')
    def max_order_qty_validation(cls, v, values):
        if v is not None and 'minimum_order_quantity' in values:
            if v < values['minimum_order_quantity']:
                raise ValueError('Maximum order quantity must be greater than or equal to minimum order quantity')
        return v
    
    @validator('expiry_date')
    def expiry_after_effective(cls, v, values):
        if v and 'effective_date' in values and values['effective_date']:
            if v <= values['effective_date']:
                raise ValueError('Expiry date must be after effective date')
        return v


class ProductSupplierCreate(ProductSupplierBase):
    """Schema for creating product supplier relationships."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "550e8400-e29b-41d4-a716-446655440001",
                "unit_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_primary_supplier": True,
                "price": "15.50",
                "minimum_order_quantity": 12,
                "lead_time_days": 3,
                "payment_terms": "Net 30"
            }
        }


class ProductSupplierUpdate(BaseModel):
    """Schema for updating product supplier relationships."""
    is_primary_supplier: Optional[bool] = None
    priority_order: Optional[int] = Field(None, ge=1)
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    minimum_order_quantity: Optional[int] = Field(None, ge=1)
    maximum_order_quantity: Optional[int] = Field(None, ge=1)
    order_multiple: Optional[int] = Field(None, ge=1)
    lead_time_days: Optional[int] = Field(None, ge=0)
    contract_reference: Optional[str] = Field(None, max_length=100)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None


class ProductSupplierResponse(ProductSupplierBase):
    """Schema for product supplier relationship responses."""
    id: UUID
    product_id: UUID
    quality_rating: Optional[Decimal] = None
    delivery_rating: Optional[Decimal] = None
    service_rating: Optional[Decimal] = None
    last_order_date: Optional[datetime] = None
    total_orders: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Calculated fields
    is_contract_active: Optional[bool] = None
    overall_rating: Optional[float] = None
    
    # Related objects (when needed)
    supplier: Optional["SupplierBasic"] = None
    unit: Optional["UnitBasic"] = None
    
    class Config:
        from_attributes = True


# Main Product Schemas

class ProductBase(BaseModel):
    """Base schema for products."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    sku: str = Field(..., min_length=1, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    category_id: Optional[UUID] = None
    unit_of_measure: str = Field("each", max_length=50)
    pack_size: int = Field(1, ge=1)
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    is_perishable: bool = False
    is_hazardous: bool = False
    requires_approval: bool = False
    is_active: bool = True
    tags: Optional[List[str]] = []
    custom_attributes: Optional[Dict[str, Any]] = {}
    
    @validator('name', 'sku')
    def name_sku_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name and SKU cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove duplicates and empty tags
            return list(set([tag.strip() for tag in v if tag.strip()]))
        return v


class ProductCreate(ProductBase):
    """Schema for creating products."""
    unit_allocations: Optional[List[ProductUnitAllocationCreate]] = []
    supplier_relationships: Optional[List[ProductSupplierCreate]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Premium Coffee Beans",
                "description": "High-quality Arabica coffee beans from Colombia",
                "sku": "COFFEE-001",
                "brand": "Colombian Gold",
                "category_id": "550e8400-e29b-41d4-a716-446655440002",
                "unit_of_measure": "kg",
                "pack_size": 5,
                "weight": "5.0",
                "is_perishable": True,
                "tags": ["premium", "organic", "fair-trade"],
                "unit_allocations": [
                    {
                        "unit_id": "550e8400-e29b-41d4-a716-446655440000",
                        "min_stock_level": 10,
                        "max_stock_level": 50,
                        "reorder_point": 15
                    }
                ]
            }
        }


class ProductUpdate(BaseModel):
    """Schema for updating products."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    brand: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    category_id: Optional[UUID] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    pack_size: Optional[int] = Field(None, ge=1)
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    is_perishable: Optional[bool] = None
    is_hazardous: Optional[bool] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    unit_allocations: Optional[List[ProductUnitAllocationCreate]] = None
    supplier_relationships: Optional[List[ProductSupplierCreate]] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class ProductResponse(ProductBase):
    """Schema for product responses."""
    id: UUID
    is_discontinued: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    
    # Relationships
    category: Optional[ProductCategoryResponse] = None
    unit_allocations: List[ProductUnitAllocationResponse] = []
    supplier_relationships: List[ProductSupplierResponse] = []
    
    # Calculated fields
    total_stock: Optional[int] = None
    units_with_low_stock: Optional[List[UUID]] = []
    average_cost: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


# Product Search and Filtering Schemas

class ProductSearchParams(BaseModel):
    """Schema for product search parameters."""
    search: Optional[str] = Field(None, min_length=2, max_length=100)
    category_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    is_active: Optional[bool] = True
    is_perishable: Optional[bool] = None
    is_hazardous: Optional[bool] = None
    requires_approval: Optional[bool] = None
    tags: Optional[List[str]] = []
    min_stock_only: bool = False  # Show only products with low stock
    
    class Config:
        json_schema_extra = {
            "example": {
                "search": "coffee",
                "category_id": "550e8400-e29b-41d4-a716-446655440002",
                "is_active": True,
                "tags": ["premium", "organic"]
            }
        }


class ProductListResponse(BaseModel):
    """Schema for paginated product list responses."""
    items: List[ProductResponse]
    total: int = 0
    page: int = 1
    per_page: int = 100
    has_next: bool = False
    has_prev: bool = False
    
    class Config:
        from_attributes = True


# Product Import/Export Schemas

class ProductImportRow(BaseModel):
    """Schema for individual product import row."""
    name: str
    sku: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    unit_of_measure: str = "each"
    supplier_code: Optional[str] = None
    price: Optional[Decimal] = None
    min_stock: Optional[int] = 0
    max_stock: Optional[int] = 100
    current_stock: Optional[int] = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Coffee Beans Premium",
                "sku": "COFFEE-001",
                "description": "Premium Arabica coffee beans",
                "category": "Food & Beverage",
                "brand": "Colombian Gold",
                "unit_of_measure": "kg",
                "supplier_code": "SUP001",
                "price": "15.50",
                "min_stock": "10",
                "max_stock": "100",
                "current_stock": "25"
            }
        }


class ProductImportResponse(BaseModel):
    """Schema for product import operation results."""
    total_imported: int = 0
    total_updated: int = 0
    total_errors: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    success: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_imported": 150,
                "total_updated": 25,
                "total_errors": 5,
                "errors": [
                    "Row 23: Invalid SKU format",
                    "Row 45: Category 'Invalid Category' not found"
                ],
                "warnings": [
                    "Row 12: Price not provided, using default"
                ],
                "success": True
            }
        }


# Stock Management Schemas

class StockUpdateRequest(BaseModel):
    """Schema for stock level updates."""
    product_id: UUID
    unit_id: UUID
    new_stock_level: int = Field(..., ge=0)
    reason: Optional[str] = Field(None, max_length=200)
    reference_number: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "550e8400-e29b-41d4-a716-446655440003",
                "unit_id": "550e8400-e29b-41d4-a716-446655440000",
                "new_stock_level": 45,
                "reason": "Stock count adjustment",
                "reference_number": "SC-2024-001"
            }
        }


class StockMovementResponse(BaseModel):
    """Schema for stock movement records."""
    id: UUID
    product_id: UUID
    unit_id: UUID
    movement_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    unit_cost: Optional[Decimal] = None
    reason: Optional[str] = None
    reference_number: Optional[str] = None
    created_at: datetime
    created_by: UUID
    
    # Related objects
    product: Optional["ProductBasic"] = None
    
    class Config:
        from_attributes = True


class LowStockAlert(BaseModel):
    """Schema for low stock alerts."""
    product_id: UUID
    product_name: str
    product_sku: str
    unit_id: UUID
    unit_name: str
    current_stock: int
    reorder_point: int
    recommended_order_quantity: int
    primary_supplier_id: Optional[UUID] = None
    primary_supplier_name: Optional[str] = None
    days_of_stock_remaining: Optional[int] = None
    
    class Config:
        from_attributes = True


# Basic Related Object Schemas

class ProductBasic(BaseModel):
    """Basic product information for references."""
    id: UUID
    name: str
    sku: str
    brand: Optional[str] = None
    unit_of_measure: str
    is_active: bool = True
    
    class Config:
        from_attributes = True


class SupplierBasic(BaseModel):
    """Basic supplier information for references."""
    id: UUID
    company_name: str
    supplier_code: str
    is_active: bool = True
    
    class Config:
        from_attributes = True


class UnitBasic(BaseModel):
    """Basic unit information for references."""
    id: UUID
    name: str
    unit_code: str
    city: Optional[str] = None
    
    class Config:
        from_attributes = True


# Inventory Report Schemas

class InventoryReportRequest(BaseModel):
    """Schema for inventory report requests."""
    unit_ids: Optional[List[UUID]] = []
    category_ids: Optional[List[UUID]] = []
    include_zero_stock: bool = False
    include_inactive: bool = False
    report_format: str = Field("summary", pattern="^(summary|detailed|valuation)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "unit_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "category_ids": ["550e8400-e29b-41d4-a716-446655440002"],
                "include_zero_stock": False,
                "report_format": "detailed"
            }
        }


class InventoryReportItem(BaseModel):
    """Schema for inventory report items."""
    product_id: UUID
    product_name: str
    product_sku: str
    category_name: Optional[str] = None
    unit_id: UUID
    unit_name: str
    current_stock: int
    min_stock_level: int
    max_stock_level: int
    reorder_point: int
    stock_value: Optional[Decimal] = None
    last_movement_date: Optional[datetime] = None
    days_since_last_movement: Optional[int] = None
    
    class Config:
        from_attributes = True


class InventoryReport(BaseModel):
    """Schema for complete inventory reports."""
    report_type: str
    generated_at: datetime
    requested_by: UUID
    unit_count: int
    product_count: int
    total_value: Optional[Decimal] = None
    items: List[InventoryReportItem]
    summary: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


# Forward reference updates for nested models
ProductCategoryResponse.model_rebuild()
ProductResponse.model_rebuild()
StockMovementResponse.model_rebuild()