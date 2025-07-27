from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
import re


class UnitBase(BaseModel):
    """Base unit schema with common fields"""
    unit_code: str = Field(..., min_length=2, max_length=10, description="Unique unit identifier")
    unit_name: str = Field(..., min_length=2, max_length=100, description="Display name of the unit")
    location: str = Field(..., min_length=2, max_length=200, description="Physical location/address")
    is_active: bool = Field(default=True, description="Whether the unit is active")
    
    @validator('unit_code')
    def validate_unit_code(cls, v):
        """Validate unit code format (alphanumeric, no spaces)"""
        if not re.match(r'^[A-Z0-9]+$', v.upper()):
            raise ValueError('Unit code must contain only letters and numbers')
        return v.upper()
    
    @validator('unit_name')
    def validate_unit_name(cls, v):
        """Ensure unit name is properly formatted"""
        return v.strip().title()


class UnitManagerContact(BaseModel):
    """Manager contact information schema"""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    position: str = Field(..., max_length=50)


class UnitBudgetSettings(BaseModel):
    """Unit budget configuration schema"""
    monthly_budget: Optional[float] = Field(None, ge=0, description="Monthly budget limit")
    emergency_threshold: Optional[float] = Field(None, ge=0, description="Emergency requisition threshold")
    approval_limit: Optional[float] = Field(None, ge=0, description="Approval required above this amount")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code format"""
        return v.upper()


class UnitOperationalSettings(BaseModel):
    """Operational settings for the unit"""
    timezone: str = Field(default="UTC", description="Unit timezone")
    business_hours_start: str = Field(default="08:00", pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    business_hours_end: str = Field(default="18:00", pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    auto_reorder_enabled: bool = Field(default=True, description="Enable automatic reordering")
    low_stock_threshold_days: int = Field(default=7, ge=1, le=90, description="Days of stock before low stock alert")


class UnitCreate(UnitBase):
    """Schema for creating a new unit"""
    manager_contact: UnitManagerContact
    budget_settings: Optional[UnitBudgetSettings] = None
    operational_settings: Optional[UnitOperationalSettings] = None


class UnitUpdate(BaseModel):
    """Schema for updating an existing unit"""
    unit_name: Optional[str] = Field(None, min_length=2, max_length=100)
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    is_active: Optional[bool] = None
    manager_contact: Optional[UnitManagerContact] = None
    budget_settings: Optional[UnitBudgetSettings] = None
    operational_settings: Optional[UnitOperationalSettings] = None
    
    @validator('unit_name')
    def validate_unit_name_update(cls, v):
        """Ensure unit name is properly formatted when updating"""
        if v is not None:
            return v.strip().title()
        return v


class UnitInDBBase(UnitBase):
    """Base schema for unit data from database"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    manager_contact: UnitManagerContact
    budget_settings: Optional[UnitBudgetSettings] = None
    operational_settings: Optional[UnitOperationalSettings] = None
    
    class Config:
        from_attributes = True


class Unit(UnitInDBBase):
    """Complete unit schema for API responses"""
    pass


class UnitInDB(UnitInDBBase):
    """Unit schema as stored in database (may include sensitive fields)"""
    pass


class UnitList(BaseModel):
    """Schema for listing units with pagination"""
    units: List[Unit]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class UnitSelector(BaseModel):
    """Simple unit schema for dropdowns and selectors"""
    id: UUID
    unit_code: str
    unit_name: str
    is_active: bool


class UnitSummary(BaseModel):
    """Unit summary with key metrics"""
    id: UUID
    unit_code: str
    unit_name: str
    location: str
    is_active: bool
    manager_name: str
    total_products: int = 0
    total_suppliers: int = 0
    pending_orders: int = 0
    monthly_spend: Optional[float] = None
    last_activity: Optional[datetime] = None


class UnitStats(BaseModel):
    """Detailed unit statistics"""
    unit_id: UUID
    total_products: int
    active_products: int
    total_suppliers: int
    active_suppliers: int
    pending_requisitions: int
    approved_requisitions: int
    total_orders_this_month: int
    total_spend_this_month: float
    average_order_value: float
    top_categories: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]


class UnitAccessRequest(BaseModel):
    """Schema for requesting access to a unit"""
    unit_id: UUID
    justification: Optional[str] = Field(None, max_length=500)


class UnitAccessResponse(BaseModel):
    """Response when switching to a unit"""
    unit: UnitSelector
    permissions: List[str]
    access_granted_at: datetime
    session_expires_at: datetime


class UnitBulkOperation(BaseModel):
    """Schema for bulk operations on units"""
    unit_ids: List[UUID] = Field(..., min_items=1, max_items=50)
    operation: str = Field(..., pattern=r'^(activate|deactivate|update_settings)$')
    data: Optional[Dict[str, Any]] = None


class UnitValidationError(BaseModel):
    """Schema for unit validation errors"""
    field: str
    message: str
    code: str


class UnitOperationResult(BaseModel):
    """Result of unit operations"""
    success: bool
    message: str
    unit_id: Optional[UUID] = None
    errors: Optional[List[UnitValidationError]] = None


# User-Unit relationship schemas
class UserUnitAssignment(BaseModel):
    """Schema for assigning users to units"""
    user_id: UUID
    unit_id: UUID
    role: str = Field(..., pattern=r'^(admin|manager|staff|viewer)$')
    permissions: List[str] = []
    assigned_at: datetime
    assigned_by: UUID
    is_active: bool = True
    
    class Config:
        from_attributes = True


class UserUnitCreate(BaseModel):
    """Schema for creating user-unit assignments"""
    user_id: UUID
    unit_id: UUID
    role: str = Field(..., pattern=r'^(admin|manager|staff|viewer)$')
    permissions: Optional[List[str]] = []


class UserUnitUpdate(BaseModel):
    """Schema for updating user-unit assignments"""
    role: Optional[str] = Field(None, pattern=r'^(admin|manager|staff|viewer)$')
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


# Response schema aliases for backward compatibility
UnitResponse = Unit  # Main response schema for API endpoints
UnitListResponse = UnitList  # For list endpoints
UnitSummaryResponse = UnitSummary  # For summary endpoints

# Additional schemas for API compatibility
UnitConfigUpdate = UnitUpdate  # Alias for config updates
UnitConfigResponse = Unit  # Alias for config response
UnitUserAssignment = UserUnitAssignment  # Alias for user assignment
UnitUserResponse = UserUnitAssignment  # Alias for user response
UnitStatsResponse = UnitStats  # Alias for stats response
UnitBudgetUpdate = UnitUpdate  # Alias for budget updates
UnitBudgetResponse = Unit  # Alias for budget response