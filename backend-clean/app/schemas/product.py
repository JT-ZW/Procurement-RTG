"""
Product schemas for the Hotel Procurement System - Enhanced E-catalogue
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID

class ProductBase(BaseModel):
    """Base product schema with E-catalogue fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    code: str = Field(..., min_length=1, max_length=100, description="Product code/SKU")
    description: Optional[str] = Field(None, description="Product full description")
    category_id: Optional[UUID] = Field(None, description="Product category ID")
    unit_of_measure: str = Field(default="pieces", description="Unit of measure")
    
    # Pricing - E-catalogue requirements
    standard_cost: Optional[float] = Field(None, ge=0, description="Standard unit price")
    contract_price: Optional[float] = Field(None, ge=0, description="Contract price (if different from standard)")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    
    # Stock management - E-catalogue requirements
    current_stock_quantity: float = Field(default=0, ge=0, description="Current stock quantity")
    minimum_stock_level: int = Field(default=0, ge=0, description="Minimum reorder level")
    maximum_stock_level: int = Field(default=1000, gt=0, description="Maximum reorder level")
    reorder_point: int = Field(default=10, ge=0, description="Reorder point")
    
    # Consumption tracking - E-catalogue requirements  
    estimated_consumption_rate_per_day: float = Field(default=0, ge=0, description="Estimated daily consumption rate")
    
    # Relationships
    unit_id: Optional[UUID] = Field(None, description="Unit/Hotel assignment")
    supplier_id: Optional[UUID] = Field(None, description="Primary supplier")
    
    # Additional specifications
    specifications: Optional[Dict[str, Any]] = Field(None, description="Additional product specifications")
    is_active: bool = Field(default=True, description="Product active status")

    @validator('maximum_stock_level')
    def validate_max_greater_than_min(cls, v, values):
        if 'minimum_stock_level' in values and v <= values['minimum_stock_level']:
            raise ValueError('Maximum stock level must be greater than minimum stock level')
        return v

    @validator('reorder_point') 
    def validate_reorder_point(cls, v, values):
        if 'minimum_stock_level' in values and v < values['minimum_stock_level']:
            raise ValueError('Reorder point should not be less than minimum stock level')
        return v

class ProductCreate(ProductBase):
    """Schema for creating a new product - all E-catalogue fields mandatory for creation"""
    name: str = Field(..., description="Product name is mandatory")
    code: str = Field(..., description="Product code is mandatory")
    unit_of_measure: str = Field(..., description="Unit of measure is mandatory")
    minimum_stock_level: int = Field(..., ge=0, description="Minimum reorder level is mandatory")
    maximum_stock_level: int = Field(..., gt=0, description="Maximum reorder level is mandatory")
    estimated_consumption_rate_per_day: float = Field(..., ge=0, description="Estimated consumption rate is mandatory")

class ProductUpdate(BaseModel):
    """Schema for updating product information"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    unit_of_measure: Optional[str] = None
    standard_cost: Optional[float] = Field(None, ge=0)
    contract_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    current_stock_quantity: Optional[float] = Field(None, ge=0)
    minimum_stock_level: Optional[int] = Field(None, ge=0)
    maximum_stock_level: Optional[int] = Field(None, gt=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    estimated_consumption_rate_per_day: Optional[float] = Field(None, ge=0)
    unit_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    """Complete product schema with computed fields for E-catalogue"""
    id: str
    
    # Computed E-catalogue fields
    effective_unit_price: Optional[float] = Field(None, description="Contract price or standard cost")
    estimated_days_stock_will_last: Optional[float] = Field(None, description="Estimated days stock will last")
    stock_status: str = Field(description="Current stock status (LOW_STOCK, REORDER_NEEDED, OVERSTOCK, NORMAL)")
    
    # Related entity information
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    unit_name: Optional[str] = None
    unit_code: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    
    # Timestamps
    last_restocked_date: Optional[str] = None
    last_consumption_update: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class ProductCategoryBase(BaseModel):
    """Base schema for product categories"""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    parent_category_id: Optional[UUID] = None
    is_active: bool = True

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryUpdate(BaseModel):
    """Schema for updating product categories"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parent_category_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class ProductCategory(ProductCategoryBase):
    """Complete product category schema"""
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

# E-catalogue specific schemas
class ECatalogueProduct(BaseModel):
    """Specialized schema for E-catalogue view with all required fields"""
    id: str
    name: str
    code: str
    description: Optional[str] = None
    category_name: Optional[str] = None
    unit_of_measure: str
    effective_unit_price: Optional[float] = None
    contract_price: Optional[float] = None
    standard_cost: Optional[float] = None
    currency: str
    current_stock_quantity: float
    minimum_stock_level: int
    maximum_stock_level: int
    reorder_point: int
    estimated_consumption_rate_per_day: float
    estimated_days_stock_will_last: Optional[float] = None
    stock_status: str
    supplier_name: Optional[str] = None
    unit_name: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: bool
    last_restocked_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StockUpdate(BaseModel):
    """Schema for updating stock levels"""
    current_stock_quantity: float = Field(..., ge=0, description="New stock quantity")
    last_restocked_date: Optional[datetime] = Field(None, description="Date of stock update")

class ConsumptionRateUpdate(BaseModel):
    """Schema for updating consumption rates"""
    estimated_consumption_rate_per_day: float = Field(..., ge=0, description="New daily consumption rate")
    last_consumption_update: Optional[datetime] = Field(None, description="Date of consumption rate update")
