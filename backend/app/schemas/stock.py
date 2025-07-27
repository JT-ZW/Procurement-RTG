"""
Stock management schemas for input validation and serialization.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum


# Enums for stock operations
class MovementType(str, Enum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"
    DAMAGE = "damage"
    EXPIRY = "expiry"


class AdjustmentReason(str, Enum):
    CYCLE_COUNT = "cycle_count"
    DAMAGE = "damage"
    EXPIRY = "expiry"
    THEFT = "theft"
    SYSTEM_CORRECTION = "system_correction"
    INITIAL_STOCK = "initial_stock"
    OTHER = "other"


# Base Stock Item Schemas
class StockItemBase(BaseModel):
    """Base stock item schema."""
    product_id: UUID
    unit_id: UUID
    current_stock: Decimal = Field(ge=0)
    reserved_stock: Decimal = Field(default=0, ge=0)
    available_stock: Decimal = Field(ge=0)
    reorder_level: Decimal = Field(default=0, ge=0)
    reorder_quantity: Decimal = Field(default=0, ge=0)
    max_stock_level: Optional[Decimal] = Field(None, ge=0)
    
    # Costing Information
    unit_cost: Decimal = Field(ge=0)
    total_value: Decimal = Field(ge=0)
    average_cost: Decimal = Field(ge=0)
    
    # Location Information
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_location: Optional[str] = Field(None, max_length=50)
    
    # Tracking Information
    track_batches: bool = Field(default=False)
    track_serial_numbers: bool = Field(default=False)
    
    @validator('available_stock', always=True)
    def calculate_available_stock(cls, v, values):
        current = values.get('current_stock', 0)
        reserved = values.get('reserved_stock', 0)
        return current - reserved


class StockItemCreate(BaseModel):
    """Schema for creating a stock item."""
    product_id: UUID
    unit_id: UUID
    initial_stock: Decimal = Field(ge=0)
    unit_cost: Decimal = Field(ge=0)
    reorder_level: Decimal = Field(default=0, ge=0)
    reorder_quantity: Decimal = Field(default=0, ge=0)
    max_stock_level: Optional[Decimal] = Field(None, ge=0)
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_location: Optional[str] = Field(None, max_length=50)


class StockItemUpdate(BaseModel):
    """Schema for updating a stock item."""
    reorder_level: Optional[Decimal] = Field(None, ge=0)
    reorder_quantity: Optional[Decimal] = Field(None, ge=0)
    max_stock_level: Optional[Decimal] = Field(None, ge=0)
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_location: Optional[str] = Field(None, max_length=50)


class StockItem(StockItemBase):
    """Complete stock item schema."""
    id: UUID
    last_movement_date: Optional[datetime] = None
    last_received_date: Optional[datetime] = None
    last_issued_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockItemDetail(StockItem):
    """Detailed stock item with related information."""
    product_name: str
    product_code: str
    unit_name: str
    batches: List['Batch'] = []
    recent_movements: List['StockMovement'] = []


# Batch/Lot Tracking Schemas
class BatchBase(BaseModel):
    """Base batch schema."""
    batch_number: str = Field(..., max_length=100)
    lot_number: Optional[str] = Field(None, max_length=100)
    manufacturing_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    supplier_batch_number: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(ge=0)
    remaining_quantity: Decimal = Field(ge=0)
    unit_cost: Decimal = Field(ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class BatchCreate(BatchBase):
    """Schema for creating a batch."""
    stock_item_id: UUID


class Batch(BatchBase):
    """Complete batch schema."""
    id: UUID
    stock_item_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Stock Movement Schemas
class StockMovementBase(BaseModel):
    """Base stock movement schema."""
    movement_type: MovementType
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    department: Optional[str] = Field(None, max_length=100)
    cost_center: Optional[str] = Field(None, max_length=100)


class StockMovementCreate(StockMovementBase):
    """Schema for creating a stock movement."""
    stock_item_id: UUID
    batch_id: Optional[UUID] = None


class StockMovement(StockMovementBase):
    """Complete stock movement schema."""
    id: UUID
    stock_item_id: UUID
    batch_id: Optional[UUID] = None
    user_id: UUID
    movement_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Stock Receiving Schemas
class StockReceivingItemBase(BaseModel):
    """Base schema for stock receiving items."""
    product_id: UUID
    ordered_quantity: Decimal = Field(gt=0)
    received_quantity: Decimal = Field(ge=0)
    unit_cost: Decimal = Field(ge=0)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    
    @validator('received_quantity')
    def validate_received_quantity(cls, v, values):
        ordered = values.get('ordered_quantity', 0)
        if v > ordered * 1.1:  # Allow 10% variance
            raise ValueError('Received quantity significantly exceeds ordered quantity')
        return v


class StockReceivingItem(StockReceivingItemBase):
    """Stock receiving item with calculated fields."""
    variance_quantity: Decimal = Field(default=0)
    variance_percentage: float = Field(default=0)
    
    @validator('variance_quantity', always=True)
    def calculate_variance_quantity(cls, v, values):
        ordered = values.get('ordered_quantity', 0)
        received = values.get('received_quantity', 0)
        return received - ordered
    
    @validator('variance_percentage', always=True)
    def calculate_variance_percentage(cls, v, values):
        ordered = values.get('ordered_quantity', 0)
        variance = values.get('variance_quantity', 0)
        if ordered > 0:
            return (variance / ordered) * 100
        return 0


class StockReceivingCreate(BaseModel):
    """Schema for creating a stock receiving record."""
    unit_id: UUID
    supplier_id: UUID
    purchase_order_number: Optional[str] = Field(None, max_length=100)
    delivery_note_number: Optional[str] = Field(None, max_length=100)
    received_date: datetime
    items: List[StockReceivingItemBase]
    notes: Optional[str] = Field(None, max_length=1000)


class StockReceiving(BaseModel):
    """Complete stock receiving schema."""
    id: UUID
    unit_id: UUID
    supplier_id: UUID
    purchase_order_number: Optional[str] = None
    delivery_note_number: Optional[str] = None
    received_date: datetime
    received_by: UUID
    total_items: int
    total_value: Decimal
    variance_count: int
    status: str = Field(default="completed")
    notes: Optional[str] = None
    created_at: datetime
    items: List[StockReceivingItem] = []
    
    class Config:
        from_attributes = True


# Stock Issuing Schemas
class StockIssuingItemBase(BaseModel):
    """Base schema for stock issuing items."""
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    batch_id: Optional[UUID] = None


class StockIssuingCreate(BaseModel):
    """Schema for creating a stock issuing record."""
    unit_id: UUID
    department: str = Field(..., max_length=100)
    cost_center: Optional[str] = Field(None, max_length=100)
    requisition_number: Optional[str] = Field(None, max_length=100)
    issued_date: datetime
    items: List[StockIssuingItemBase]
    notes: Optional[str] = Field(None, max_length=1000)


class StockIssuing(BaseModel):
    """Complete stock issuing schema."""
    id: UUID
    unit_id: UUID
    department: str
    cost_center: Optional[str] = None
    requisition_number: Optional[str] = None
    issued_date: datetime
    issued_by: UUID
    total_items: int
    total_value: Decimal
    status: str = Field(default="completed")
    notes: Optional[str] = None
    created_at: datetime
    items: List[StockIssuingItemBase] = []
    
    class Config:
        from_attributes = True


# Stock Adjustment Schemas
class StockAdjustmentItemBase(BaseModel):
    """Base schema for stock adjustment items."""
    product_id: UUID
    system_quantity: Decimal = Field(ge=0)
    actual_quantity: Decimal = Field(ge=0)
    unit_cost: Decimal = Field(ge=0)
    batch_id: Optional[UUID] = None
    
    @property
    def adjustment_quantity(self) -> Decimal:
        return self.actual_quantity - self.system_quantity
    
    @property
    def adjustment_value(self) -> Decimal:
        return self.adjustment_quantity * self.unit_cost


class StockAdjustmentCreate(BaseModel):
    """Schema for creating a stock adjustment."""
    unit_id: UUID
    reason: AdjustmentReason
    reference_number: Optional[str] = Field(None, max_length=100)
    adjustment_date: datetime
    items: List[StockAdjustmentItemBase]
    notes: Optional[str] = Field(None, max_length=1000)


class StockAdjustment(BaseModel):
    """Complete stock adjustment schema."""
    id: UUID
    unit_id: UUID
    reason: AdjustmentReason
    reference_number: Optional[str] = None
    adjustment_date: datetime
    adjusted_by: UUID
    total_items: int
    total_adjustment_value: Decimal
    positive_adjustments: int
    negative_adjustments: int
    status: str = Field(default="completed")
    notes: Optional[str] = None
    created_at: datetime
    items: List[StockAdjustmentItemBase] = []
    
    class Config:
        from_attributes = True


# Stock Transfer Schemas
class StockTransferItemBase(BaseModel):
    """Base schema for stock transfer items."""
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    batch_id: Optional[UUID] = None


class StockTransferCreate(BaseModel):
    """Schema for creating a stock transfer."""
    from_unit_id: UUID
    to_unit_id: UUID
    transfer_date: datetime
    reference_number: Optional[str] = Field(None, max_length=100)
    items: List[StockTransferItemBase]
    notes: Optional[str] = Field(None, max_length=1000)


class StockTransfer(BaseModel):
    """Complete stock transfer schema."""
    id: UUID
    from_unit_id: UUID
    to_unit_id: UUID
    transfer_date: datetime
    initiated_by: UUID
    received_by: Optional[UUID] = None
    reference_number: Optional[str] = None
    total_items: int
    total_value: Decimal
    status: str = Field(default="pending", pattern="^(pending|in_transit|completed|cancelled)$")
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    items: List[StockTransferItemBase] = []
    
    class Config:
        from_attributes = True


# Reorder and Alerts Schemas
class ReorderAlert(BaseModel):
    """Reorder alert schema."""
    stock_item_id: UUID
    product_id: UUID
    product_name: str
    product_code: str
    unit_id: UUID
    unit_name: str
    current_stock: Decimal
    reorder_level: Decimal
    reorder_quantity: Decimal
    days_out_of_stock: int
    priority: str = Field(pattern="^(low|medium|high|urgent)$")
    suggested_order_quantity: Decimal
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = None
    lead_time_days: Optional[int] = None


class AutoReorderRequest(BaseModel):
    """Auto reorder request schema."""
    unit_id: UUID
    product_ids: Optional[List[UUID]] = None
    priority_threshold: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    max_orders: int = Field(default=50, ge=1, le=100)


class AutoReorderResult(BaseModel):
    """Auto reorder result schema."""
    processed_items: int
    orders_created: int
    orders_failed: int
    total_value: Decimal
    reorder_items: List[Dict[str, Any]]
    errors: List[str]


# Batch Traceability and Recall Schemas
class BatchTraceability(BaseModel):
    """Batch traceability information."""
    batch_id: UUID
    batch_number: str
    product_name: str
    supplier_name: str
    manufacturing_date: Optional[datetime]
    expiry_date: Optional[datetime]
    received_date: datetime
    movements: List[StockMovement]
    current_locations: List[Dict[str, Any]]
    consumed_departments: List[str]


class BatchRecallCreate(BaseModel):
    """Schema for creating a batch recall."""
    reason: str = Field(..., max_length=500)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    action_required: str = Field(..., max_length=1000)
    contact_customers: bool = Field(default=False)


class BatchRecall(BaseModel):
    """Complete batch recall schema."""
    id: UUID
    batch_id: UUID
    reason: str
    severity: str
    action_required: str
    contact_customers: bool
    initiated_by: UUID
    initiated_date: datetime
    status: str = Field(default="active", pattern="^(active|completed|cancelled)$")
    affected_units: List[Dict[str, Any]]
    recovery_progress: Dict[str, Any]
    
    class Config:
        from_attributes = True


# Reports and Analytics Schemas
class StockValuationReport(BaseModel):
    """Stock valuation report schema."""
    report_date: datetime
    valuation_method: str
    total_value: Decimal
    total_items: int
    categories: List[Dict[str, Any]]
    units: List[Dict[str, Any]]
    top_value_items: List[Dict[str, Any]]


class StockMovementReport(BaseModel):
    """Stock movement report schema."""
    period_start: datetime
    period_end: datetime
    total_movements: int
    receipts: Dict[str, Any]
    issues: Dict[str, Any]
    adjustments: Dict[str, Any]
    transfers: Dict[str, Any]
    movement_trends: List[Dict[str, Any]]


class DeadStockReport(BaseModel):
    """Dead stock report schema."""
    analysis_date: datetime
    days_threshold: int
    total_dead_stock_value: Decimal
    total_dead_stock_items: int
    items: List[Dict[str, Any]]
    recommendations: List[str]


class StockDashboard(BaseModel):
    """Stock dashboard schema."""
    total_value: Decimal
    total_items: int
    low_stock_alerts: int
    expiring_items: int
    recent_movements: List[StockMovement]
    top_moving_items: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


# List and Pagination Schemas
class StockInventoryList(BaseModel):
    """Paginated stock inventory list."""
    items: List[StockItem]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class StockReceivingList(BaseModel):
    """Paginated stock receiving list."""
    receivings: List[StockReceiving]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class StockIssuingList(BaseModel):
    """Paginated stock issuing list."""
    issuings: List[StockIssuing]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class StockAdjustmentList(BaseModel):
    """Paginated stock adjustment list."""
    adjustments: List[StockAdjustment]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class BatchList(BaseModel):
    """Paginated batch list."""
    batches: List[Batch]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ReorderAlertList(BaseModel):
    """List of reorder alerts."""
    alerts: List[ReorderAlert]
    total: int
    high_priority_count: int
    urgent_count: int
