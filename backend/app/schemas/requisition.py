"""
Purchase Requisition Pydantic Schemas
Data validation and serialization schemas for purchase requisitions.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, model_validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from app.models.purchase_requisition import RequisitionStatus, RequisitionPriority


# ========== BASE SCHEMAS ==========

class RequisitionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Requisition title")
    description: Optional[str] = Field(None, description="Detailed description")
    unit_id: str = Field(..., description="Unit ID for multi-tenant access")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    cost_center: Optional[str] = Field(None, max_length=50, description="Cost center")
    project_code: Optional[str] = Field(None, max_length=50, description="Project code")
    priority: RequisitionPriority = Field(RequisitionPriority.MEDIUM, description="Requisition priority")
    required_by_date: datetime = Field(..., description="Date when items are required")
    business_justification: str = Field(..., min_length=10, description="Business justification")
    expected_benefit: Optional[str] = Field(None, description="Expected benefits")
    risk_if_not_approved: Optional[str] = Field(None, description="Risks if not approved")
    estimated_total_value: Decimal = Field(..., ge=0, description="Estimated total value")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    budget_line_item: Optional[str] = Field(None, max_length=100, description="Budget line item")
    preferred_supplier_id: Optional[str] = Field(None, description="Preferred supplier ID")
    supplier_selection_justification: Optional[str] = Field(None, description="Supplier selection reason")
    quotes_required: bool = Field(True, description="Whether quotes are required")
    min_quotes_required: int = Field(3, ge=1, description="Minimum quotes required")
    delivery_location: Optional[str] = Field(None, max_length=200, description="Delivery location")
    delivery_instructions: Optional[str] = Field(None, description="Special delivery instructions")
    delivery_contact_person: Optional[str] = Field(None, max_length=200, description="Delivery contact")
    delivery_contact_phone: Optional[str] = Field(None, max_length=50, description="Delivery phone")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")

    @validator('currency')
    def validate_currency(cls, v):
        if not v.isupper() or len(v) != 3:
            raise ValueError('Currency must be a 3-letter uppercase code')
        return v

    @validator('required_by_date')
    def validate_required_date(cls, v):
        if v <= datetime.now():
            raise ValueError('Required by date must be in the future')
        return v

    class Config:
        use_enum_values = True


class RequisitionCreate(RequisitionBase):
    """Schema for creating a new requisition."""
    pass


class RequisitionUpdate(BaseModel):
    """Schema for updating an existing requisition."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    cost_center: Optional[str] = Field(None, max_length=50)
    project_code: Optional[str] = Field(None, max_length=50)
    priority: Optional[RequisitionPriority] = None
    required_by_date: Optional[datetime] = None
    business_justification: Optional[str] = Field(None, min_length=10)
    expected_benefit: Optional[str] = None
    risk_if_not_approved: Optional[str] = None
    estimated_total_value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    budget_line_item: Optional[str] = Field(None, max_length=100)
    preferred_supplier_id: Optional[str] = None
    supplier_selection_justification: Optional[str] = None
    quotes_required: Optional[bool] = None
    min_quotes_required: Optional[int] = Field(None, ge=1)
    delivery_location: Optional[str] = Field(None, max_length=200)
    delivery_instructions: Optional[str] = None
    delivery_contact_person: Optional[str] = Field(None, max_length=200)
    delivery_contact_phone: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @validator('currency')
    def validate_currency(cls, v):
        if v is not None and (not v.isupper() or len(v) != 3):
            raise ValueError('Currency must be a 3-letter uppercase code')
        return v

    @validator('required_by_date')
    def validate_required_date(cls, v):
        if v is not None and v <= datetime.now():
            raise ValueError('Required by date must be in the future')
        return v

    class Config:
        use_enum_values = True


class RequisitionStatusUpdate(BaseModel):
    """Schema for updating requisition status."""
    status: RequisitionStatus
    comments: Optional[str] = None

    class Config:
        use_enum_values = True


# ========== REQUISITION ITEM SCHEMAS ==========

class RequisitionItemBase(BaseModel):
    product_id: Optional[str] = Field(None, description="Product ID if from catalog")
    product_code: Optional[str] = Field(None, max_length=100, description="Product code")
    product_name: str = Field(..., min_length=1, max_length=200, description="Product name")
    product_description: Optional[str] = Field(None, description="Product description")
    quantity_requested: Decimal = Field(..., gt=0, description="Requested quantity")
    unit_of_measure: str = Field(..., min_length=1, max_length=50, description="Unit of measure")
    estimated_unit_price: Optional[Decimal] = Field(None, ge=0, description="Estimated unit price")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    technical_specifications: Optional[str] = Field(None, description="Technical specifications")
    quality_requirements: Optional[str] = Field(None, description="Quality requirements")
    brand_preference: Optional[str] = Field(None, max_length=100, description="Preferred brand")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    preferred_supplier_id: Optional[str] = Field(None, description="Preferred supplier ID")
    supplier_part_number: Optional[str] = Field(None, max_length=100, description="Supplier part number")
    delivery_date_required: Optional[datetime] = Field(None, description="Required delivery date")
    delivery_location: Optional[str] = Field(None, max_length=200, description="Delivery location")
    special_delivery_instructions: Optional[str] = Field(None, description="Special instructions")
    account_code: Optional[str] = Field(None, max_length=50, description="Account code")
    cost_center: Optional[str] = Field(None, max_length=50, description="Cost center")
    project_code: Optional[str] = Field(None, max_length=50, description="Project code")

    @validator('currency')
    def validate_currency(cls, v):
        if not v.isupper() or len(v) != 3:
            raise ValueError('Currency must be a 3-letter uppercase code')
        return v

    @model_validator(mode='after')
    def validate_product_info(self):
        if not self.product_id and not self.product_code:
            raise ValueError('Either product_id or product_code must be provided')
        return self

    class Config:
        use_enum_values = True


class RequisitionItemCreate(RequisitionItemBase):
    """Schema for creating a requisition item."""
    pass


class RequisitionItemUpdate(BaseModel):
    """Schema for updating a requisition item."""
    product_id: Optional[str] = None
    product_code: Optional[str] = Field(None, max_length=100)
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_description: Optional[str] = None
    quantity_requested: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, min_length=1, max_length=50)
    estimated_unit_price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    technical_specifications: Optional[str] = None
    quality_requirements: Optional[str] = None
    brand_preference: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    preferred_supplier_id: Optional[str] = None
    supplier_part_number: Optional[str] = Field(None, max_length=100)
    delivery_date_required: Optional[datetime] = None
    delivery_location: Optional[str] = Field(None, max_length=200)
    special_delivery_instructions: Optional[str] = None
    account_code: Optional[str] = Field(None, max_length=50)
    cost_center: Optional[str] = Field(None, max_length=50)
    project_code: Optional[str] = Field(None, max_length=50)

    @validator('currency')
    def validate_currency(cls, v):
        if v is not None and (not v.isupper() or len(v) != 3):
            raise ValueError('Currency must be a 3-letter uppercase code')
        return v

    class Config:
        use_enum_values = True


class RequisitionItemResponse(RequisitionItemBase):
    """Schema for requisition item responses."""
    id: str
    requisition_id: str
    line_number: int
    quantity_approved: Optional[Decimal] = None
    quantity_fulfilled: Decimal = Field(default=0)
    estimated_total_price: Optional[Decimal] = None
    approved_unit_price: Optional[Decimal] = None
    approved_total_price: Optional[Decimal] = None
    item_status: str = Field(default="pending")
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== APPROVAL SCHEMAS ==========

class RequisitionApprovalBase(BaseModel):
    comments: Optional[str] = Field(None, description="Approval comments")
    conditions: Optional[str] = Field(None, description="Approval conditions")
    approved_amount: Optional[Decimal] = Field(None, ge=0, description="Approved amount")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    budget_impact_notes: Optional[str] = Field(None, description="Budget impact notes")

    @validator('currency')
    def validate_currency(cls, v):
        if not v.isupper() or len(v) != 3:
            raise ValueError('Currency must be a 3-letter uppercase code')
        return v

    class Config:
        use_enum_values = True


class RequisitionApprovalCreate(RequisitionApprovalBase):
    """Schema for creating an approval record."""
    pass


class RequisitionApprovalResponse(RequisitionApprovalBase):
    """Schema for approval responses."""
    id: str
    requisition_id: str
    approval_level: int
    approver_id: str
    approver_role: str
    decision: str
    decision_date: datetime
    escalated_from: Optional[str] = None
    escalation_reason: Optional[str] = None
    delegated_by: Optional[str] = None
    delegation_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== COMMENT SCHEMAS ==========

class RequisitionCommentBase(BaseModel):
    comment_text: str = Field(..., min_length=1, description="Comment text")
    comment_type: str = Field("general", description="Comment type")
    is_internal: bool = Field(True, description="Internal comment flag")
    requires_response: bool = Field(False, description="Requires response flag")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for replies")

    @validator('comment_type')
    def validate_comment_type(cls, v):
        allowed_types = ["general", "approval", "clarification", "system"]
        if v not in allowed_types:
            raise ValueError(f'Comment type must be one of: {", ".join(allowed_types)}')
        return v

    class Config:
        use_enum_values = True


class RequisitionCommentCreate(RequisitionCommentBase):
    """Schema for creating a comment."""
    pass


class RequisitionCommentResponse(RequisitionCommentBase):
    """Schema for comment responses."""
    id: str
    requisition_id: str
    author_id: str
    author_role: Optional[str] = None
    is_system_generated: bool = Field(default=False)
    notification_sent: bool = Field(default=False)
    thread_id: str
    is_resolved: bool = Field(default=False)
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = Field(default=False)

    # Related data
    author_name: Optional[str] = None
    resolver_name: Optional[str] = None

    class Config:
        from_attributes = True


# ========== MAIN RESPONSE SCHEMAS ==========

class RequisitionResponse(RequisitionBase):
    """Schema for requisition responses."""
    id: str
    requisition_number: str
    status: RequisitionStatus
    requested_by: str
    requested_date: datetime
    approval_level: int = Field(default=1)
    requires_approval_levels: int = Field(default=1)
    current_approver_id: Optional[str] = None
    
    # Status timestamps
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Rejection/cancellation details
    rejection_reason: Optional[str] = None
    rejection_comments: Optional[str] = None
    rejected_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    
    # Processing information
    converted_to_po_at: Optional[datetime] = None
    purchase_order_numbers: Optional[List[str]] = None
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Soft delete
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    
    # Related data
    requestor_name: Optional[str] = None
    unit_name: Optional[str] = None
    current_approver_name: Optional[str] = None
    preferred_supplier_name: Optional[str] = None
    
    # Child relationships
    items: List[RequisitionItemResponse] = Field(default_factory=list)
    approvals: List[RequisitionApprovalResponse] = Field(default_factory=list)
    comments_count: int = Field(default=0)
    
    class Config:
        from_attributes = True
        use_enum_values = True


class RequisitionListResponse(BaseModel):
    """Schema for paginated requisition list responses."""
    items: List[RequisitionResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


# ========== SUMMARY SCHEMAS ==========

class RequisitionSummary(BaseModel):
    """Lightweight schema for requisition summaries."""
    id: str
    requisition_number: str
    title: str
    status: RequisitionStatus
    priority: RequisitionPriority
    estimated_total_value: Decimal
    currency: str
    requested_by: str
    requestor_name: Optional[str] = None
    requested_date: datetime
    required_by_date: datetime
    unit_id: str
    unit_name: Optional[str] = None
    items_count: int = Field(default=0)
    current_approver_name: Optional[str] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


# ========== DASHBOARD SCHEMAS ==========

class RequisitionStats(BaseModel):
    """Schema for requisition statistics."""
    total_requisitions: int = 0
    draft_count: int = 0
    submitted_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    fulfilled_count: int = 0
    cancelled_count: int = 0
    total_value: Decimal = Field(default=0)
    average_approval_time_hours: Optional[float] = None
    
    class Config:
        use_enum_values = True


class RequisitionDashboard(BaseModel):
    """Schema for requisition dashboard data."""
    stats: RequisitionStats
    pending_approvals: List[RequisitionSummary] = Field(default_factory=list)
    recent_requisitions: List[RequisitionSummary] = Field(default_factory=list)
    urgent_requisitions: List[RequisitionSummary] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


# ========== WORKFLOW SCHEMAS ==========

class RequisitionWorkflowAction(BaseModel):
    """Schema for workflow actions."""
    action: str = Field(..., description="Action to perform")
    comments: Optional[str] = Field(None, description="Action comments")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["submit", "approve", "reject", "return", "cancel"]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v
    
    class Config:
        use_enum_values = True


class RequisitionBulkAction(BaseModel):
    """Schema for bulk actions on requisitions."""
    requisition_ids: List[str] = Field(..., min_items=1, description="List of requisition IDs")
    action: str = Field(..., description="Bulk action to perform")
    comments: Optional[str] = Field(None, description="Action comments")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["approve", "reject", "cancel", "delete"]
        if v not in allowed_actions:
            raise ValueError(f'Bulk action must be one of: {", ".join(allowed_actions)}')
        return v
    
    class Config:
        use_enum_values = True
