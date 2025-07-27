"""
Supplier schemas for input validation and serialization.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# Base Supplier Schemas
class SupplierBase(BaseModel):
    """Base supplier schema with common fields."""
    supplier_code: str = Field(..., min_length=2, max_length=20)
    company_name: str = Field(..., min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Contact Information
    primary_contact_name: str = Field(..., max_length=100)
    primary_contact_title: Optional[str] = Field(None, max_length=100)
    primary_email: EmailStr
    primary_phone: str = Field(..., max_length=20)
    secondary_email: Optional[EmailStr] = None
    secondary_phone: Optional[str] = Field(None, max_length=20)
    
    # Address Information
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state_province: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=100)
    
    # Business Information
    business_type: str = Field(..., pattern="^(corporation|llc|partnership|sole_proprietorship|other)$")
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    
    # Supplier Categories
    categories: List[str] = Field(default_factory=list)
    
    # Payment and Terms
    payment_terms: str = Field(default="net_30", pattern="^(net_15|net_30|net_45|net_60|cash|cod)$")
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    discount_terms: Optional[str] = Field(None, max_length=100)
    
    # Operational Information
    lead_time_days: int = Field(default=7, ge=1, le=365)
    minimum_order_value: Optional[Decimal] = Field(None, ge=0)
    delivery_zones: List[str] = Field(default_factory=list)
    delivery_schedule: Optional[str] = Field(None, max_length=255)
    
    # Quality and Compliance
    certifications: List[str] = Field(default_factory=list)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    compliance_status: str = Field(default="pending", pattern="^(compliant|non_compliant|pending|under_review)$")
    
    # Status
    status: str = Field(default="pending", pattern="^(active|inactive|pending|suspended|blacklisted)$")
    
    @validator('categories', 'delivery_zones', 'certifications')
    def validate_lists(cls, v):
        if v is None:
            return []
        return v


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating an existing supplier."""
    supplier_code: Optional[str] = Field(None, min_length=2, max_length=20)
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Contact Information
    primary_contact_name: Optional[str] = Field(None, max_length=100)
    primary_contact_title: Optional[str] = Field(None, max_length=100)
    primary_email: Optional[EmailStr] = None
    primary_phone: Optional[str] = Field(None, max_length=20)
    secondary_email: Optional[EmailStr] = None
    secondary_phone: Optional[str] = Field(None, max_length=20)
    
    # Address Information
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Business Information
    business_type: Optional[str] = Field(None, pattern="^(corporation|llc|partnership|sole_proprietorship|other)$")
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    
    # Supplier Categories
    categories: Optional[List[str]] = None
    
    # Payment and Terms
    payment_terms: Optional[str] = Field(None, pattern="^(net_15|net_30|net_45|net_60|cash|cod)$")
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    discount_terms: Optional[str] = Field(None, max_length=100)
    
    # Operational Information
    lead_time_days: Optional[int] = Field(None, ge=1, le=365)
    minimum_order_value: Optional[Decimal] = Field(None, ge=0)
    delivery_zones: Optional[List[str]] = None
    delivery_schedule: Optional[str] = Field(None, max_length=255)
    
    # Quality and Compliance
    certifications: Optional[List[str]] = None
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    compliance_status: Optional[str] = Field(None, pattern="^(compliant|non_compliant|pending|under_review)$")
    
    # Status
    status: Optional[str] = Field(None, pattern="^(active|inactive|pending|suspended|blacklisted)$")


class SupplierInDB(SupplierBase):
    """Supplier schema with database fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID] = None
    
    # Performance Metrics
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    total_orders: int = Field(default=0)
    successful_deliveries: int = Field(default=0)
    on_time_deliveries: int = Field(default=0)
    quality_issues: int = Field(default=0)
    
    # Financial Information
    total_spent: Decimal = Field(default=0)
    outstanding_balance: Decimal = Field(default=0)
    last_order_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Supplier(SupplierInDB):
    """Complete supplier schema for API responses."""
    pass


# Contact Schemas
class SupplierContactBase(BaseModel):
    """Base schema for supplier contacts."""
    contact_type: str = Field(..., pattern="^(primary|billing|shipping|technical|emergency)$")
    name: str = Field(..., max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)


class SupplierContactCreate(SupplierContactBase):
    """Schema for creating supplier contact."""
    supplier_id: UUID


class SupplierContactUpdate(BaseModel):
    """Schema for updating supplier contact."""
    contact_type: Optional[str] = Field(None, pattern="^(primary|billing|shipping|technical|emergency)$")
    name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class SupplierContact(SupplierContactBase):
    """Complete supplier contact schema."""
    id: UUID
    supplier_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Performance and Evaluation Schemas
class SupplierPerformanceMetrics(BaseModel):
    """Supplier performance metrics."""
    supplier_id: UUID
    period_start: datetime
    period_end: datetime
    
    # Delivery Performance
    total_orders: int
    on_time_deliveries: int
    late_deliveries: int
    cancelled_orders: int
    on_time_percentage: float
    
    # Quality Performance
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    defect_rate: float = Field(ge=0, le=100)
    return_rate: float = Field(ge=0, le=100)
    
    # Financial Performance
    total_value: Decimal
    average_order_value: Decimal
    cost_savings: Optional[Decimal] = None
    
    # Overall Performance
    overall_score: float = Field(ge=0, le=100)
    rating: str = Field(pattern="^(excellent|good|satisfactory|poor|unacceptable)$")
    
    class Config:
        from_attributes = True


class SupplierEvaluationBase(BaseModel):
    """Base schema for supplier evaluation."""
    evaluation_period: str = Field(..., pattern="^(monthly|quarterly|annual)$")
    evaluation_date: datetime
    evaluator_id: UUID
    
    # Evaluation Criteria (1-5 scale)
    quality_score: int = Field(..., ge=1, le=5)
    delivery_score: int = Field(..., ge=1, le=5)
    service_score: int = Field(..., ge=1, le=5)
    price_competitiveness: int = Field(..., ge=1, le=5)
    communication_score: int = Field(..., ge=1, le=5)
    compliance_score: int = Field(..., ge=1, le=5)
    
    # Comments and Recommendations
    strengths: Optional[str] = Field(None, max_length=1000)
    weaknesses: Optional[str] = Field(None, max_length=1000)
    improvement_areas: Optional[str] = Field(None, max_length=1000)
    recommendations: Optional[str] = Field(None, max_length=1000)
    
    # Overall Assessment
    overall_score: float = Field(ge=1, le=5)
    recommendation: str = Field(..., pattern="^(continue|improve|review|discontinue)$")


class SupplierEvaluationCreate(SupplierEvaluationBase):
    """Schema for creating supplier evaluation."""
    supplier_id: UUID


class SupplierEvaluation(SupplierEvaluationBase):
    """Complete supplier evaluation schema."""
    id: UUID
    supplier_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# List and Pagination Schemas
class SupplierList(BaseModel):
    """Paginated list of suppliers."""
    suppliers: List[Supplier]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class SupplierContactList(BaseModel):
    """List of supplier contacts."""
    contacts: List[SupplierContact]
    total: int


class SupplierPerformanceList(BaseModel):
    """List of supplier performance metrics."""
    metrics: List[SupplierPerformanceMetrics]
    total: int


class SupplierEvaluationList(BaseModel):
    """List of supplier evaluations."""
    evaluations: List[SupplierEvaluation]
    total: int


# Dashboard and Reports
class SupplierDashboard(BaseModel):
    """Supplier dashboard data."""
    total_suppliers: int
    active_suppliers: int
    pending_suppliers: int
    top_performers: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    recent_evaluations: List[SupplierEvaluation]
    alerts: List[Dict[str, Any]]


class SupplierReport(BaseModel):
    """Comprehensive supplier report."""
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    data: Dict[str, Any]
    summary: Dict[str, Any]


# Import/Export Schemas
class SupplierImport(BaseModel):
    """Schema for bulk supplier import."""
    suppliers: List[SupplierCreate]
    validate_only: bool = Field(default=False)
    update_existing: bool = Field(default=False)


class SupplierImportResult(BaseModel):
    """Result of supplier import operation."""
    total_processed: int
    successful_imports: int
    failed_imports: int
    updated_records: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


# Search and Filter Schemas
class SupplierSearchFilters(BaseModel):
    """Advanced search filters for suppliers."""
    search_term: Optional[str] = None
    categories: Optional[List[str]] = None
    status: Optional[List[str]] = None
    business_types: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    min_performance_score: Optional[float] = Field(None, ge=0, le=100)
    max_performance_score: Optional[float] = Field(None, ge=0, le=100)
    has_certifications: Optional[List[str]] = None
    min_credit_limit: Optional[Decimal] = None
    max_lead_time: Optional[int] = None
    
    class Config:
        extra = "forbid"


# Additional missing schemas for API routes
class SupplierContract(BaseModel):
    """Supplier contract schema."""
    id: UUID
    supplier_id: UUID
    contract_number: str
    start_date: datetime
    end_date: datetime
    status: str
    value: Decimal
    terms: Optional[str] = None
    
    class Config:
        from_attributes = True


class SupplierContractCreate(BaseModel):
    """Schema for creating supplier contract."""
    contract_number: str
    start_date: datetime
    end_date: datetime
    value: Decimal
    terms: Optional[str] = None
    unit_assignments: List[UUID] = Field(default_factory=list)


class SupplierPerformance(BaseModel):
    """Supplier performance schema."""
    supplier_id: UUID
    performance_score: float
    on_time_delivery_rate: float
    quality_score: float
    total_orders: int
    period_start: datetime
    period_end: datetime
    
    class Config:
        from_attributes = True


class SupplierUnitAssignment(BaseModel):
    """Schema for assigning supplier to units."""
    unit_ids: List[UUID]


class BulkOperationResult(BaseModel):
    """Result of bulk operations."""
    successful_operations: int
    failed_operations: int
    total_processed: int
    errors: List[str] = Field(default_factory=list)


class SupplierBulkOperation(BaseModel):
    """Schema for bulk operations on suppliers."""
    supplier_ids: List[UUID]
    operation: str  # activate, deactivate, delete, etc.
    data: Optional[Dict[str, Any]] = None


class SupplierStats(BaseModel):
    """Supplier statistics schema."""
    total_suppliers: int
    active_suppliers: int
    inactive_suppliers: int
    pending_suppliers: int
    average_performance_score: Optional[float] = None
    top_performers: List[Dict[str, Any]] = Field(default_factory=list)
