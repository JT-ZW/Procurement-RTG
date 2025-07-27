"""
Purchase Requisition Models
Handles requests for procurement of goods/services with approval workflow.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Enum, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from decimal import Decimal
import enum

from app.core.database import Base


class RequisitionStatus(str, enum.Enum):
    """Enumeration of possible requisition statuses."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class RequisitionPriority(str, enum.Enum):
    """Enumeration of requisition priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class PurchaseRequisition(Base):
    """
    Main purchase requisition model.
    Central entity for procurement requests with approval workflow.
    """
    __tablename__ = "purchase_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    requisition_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Multi-tenant & organization
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, index=True)
    department = Column(String(100), index=True)
    cost_center = Column(String(50), index=True)
    project_code = Column(String(50), index=True)
    
    # Request details
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.DRAFT, nullable=False, index=True)
    priority = Column(Enum(RequisitionPriority), default=RequisitionPriority.MEDIUM, nullable=False)
    
    # Requestor information
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    required_by_date = Column(DateTime(timezone=True), nullable=False)
    
    # Business justification
    business_justification = Column(Text, nullable=False)
    expected_benefit = Column(Text)
    risk_if_not_approved = Column(Text)
    
    # Financial information
    estimated_total_value = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    budget_line_item = Column(String(100))
    budget_remaining = Column(Numeric(15, 2))
    
    # Approval workflow
    approval_level = Column(Integer, default=1)  # Current approval level
    requires_approval_levels = Column(Integer, default=1)  # Total levels needed
    current_approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Supplier preferences
    preferred_supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    supplier_selection_justification = Column(Text)
    quotes_required = Column(Boolean, default=True)
    min_quotes_required = Column(Integer, default=3)
    
    # Delivery information
    delivery_location = Column(String(200))
    delivery_instructions = Column(Text)
    delivery_contact_person = Column(String(200))
    delivery_contact_phone = Column(String(50))
    
    # Status tracking
    submitted_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    fulfilled_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Rejection/cancellation details
    rejection_reason = Column(Text)
    rejection_comments = Column(Text)
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    cancellation_reason = Column(Text)
    cancelled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Processing information
    converted_to_po_at = Column(DateTime(timezone=True))
    purchase_order_numbers = Column(JSONB)  # List of generated PO numbers
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    tags = Column(JSONB)  # For categorization and searching
    attachments = Column(JSONB)  # File attachments metadata
    custom_fields = Column(JSONB)  # Unit-specific custom fields
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    requestor = relationship("User", foreign_keys=[requested_by])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    preferred_supplier = relationship("Supplier")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    rejecter = relationship("User", foreign_keys=[rejected_by])
    canceller = relationship("User", foreign_keys=[cancelled_by])
    
    # Child relationships
    items = relationship("RequisitionItem", back_populates="requisition", cascade="all, delete-orphan")
    approvals = relationship("RequisitionApproval", back_populates="requisition", cascade="all, delete-orphan")
    comments = relationship("RequisitionComment", back_populates="requisition", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("estimated_total_value >= 0", name='chk_requisition_value_non_negative'),
        CheckConstraint("approval_level >= 1", name='chk_requisition_approval_level_valid'),
        CheckConstraint("requires_approval_levels >= 1", name='chk_requisition_approval_levels_valid'),
        CheckConstraint("min_quotes_required >= 1", name='chk_requisition_min_quotes_valid'),
        CheckConstraint("required_by_date > requested_date", name='chk_requisition_dates_valid'),
        Index('idx_requisition_unit_status', 'unit_id', 'status'),
        Index('idx_requisition_requestor_date', 'requested_by', 'requested_date'),
        Index('idx_requisition_approver', 'current_approver_id'),
        Index('idx_requisition_required_date', 'required_by_date'),
        Index('idx_requisition_cost_center', 'cost_center'),
        Index('idx_requisition_department', 'department'),
    )


class RequisitionItem(Base):
    """
    Individual items within a purchase requisition.
    Links to products and specifies quantities and specifications.
    """
    __tablename__ = "requisition_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent requisition
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=False, index=True)
    
    # Item details
    line_number = Column(Integer, nullable=False)  # Item sequence in requisition
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    product_code = Column(String(100))  # If no product_id, manual entry
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text)
    
    # Quantity and units
    quantity_requested = Column(Numeric(15, 3), nullable=False)
    quantity_approved = Column(Numeric(15, 3))
    quantity_fulfilled = Column(Numeric(15, 3), default=0)
    unit_of_measure = Column(String(50), nullable=False)
    
    # Pricing
    estimated_unit_price = Column(Numeric(12, 2))
    estimated_total_price = Column(Numeric(15, 2))
    approved_unit_price = Column(Numeric(12, 2))
    approved_total_price = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    
    # Specifications
    technical_specifications = Column(Text)
    quality_requirements = Column(Text)
    brand_preference = Column(String(100))
    model_number = Column(String(100))
    
    # Supplier information
    preferred_supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    supplier_part_number = Column(String(100))
    
    # Delivery requirements
    delivery_date_required = Column(DateTime(timezone=True))
    delivery_location = Column(String(200))
    special_delivery_instructions = Column(Text)
    
    # Status tracking
    item_status = Column(String(50), default="pending")  # "pending", "approved", "rejected", "fulfilled"
    approval_notes = Column(Text)
    rejection_reason = Column(Text)
    
    # Accounting
    account_code = Column(String(50))
    cost_center = Column(String(50))
    project_code = Column(String(50))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requisition = relationship("PurchaseRequisition", back_populates="items")
    product = relationship("Product")
    preferred_supplier = relationship("Supplier")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique line numbers within a requisition
        Index('idx_requisition_item_line', 'requisition_id', 'line_number', unique=True),
        CheckConstraint("quantity_requested > 0", name='chk_requisition_item_quantity_positive'),
        CheckConstraint("quantity_approved IS NULL OR quantity_approved >= 0", name='chk_requisition_item_approved_quantity'),
        CheckConstraint("quantity_fulfilled >= 0", name='chk_requisition_item_fulfilled_quantity'),
        CheckConstraint("estimated_unit_price IS NULL OR estimated_unit_price >= 0", name='chk_requisition_item_price_non_negative'),
        Index('idx_requisition_item_product', 'product_id'),
        Index('idx_requisition_item_supplier', 'preferred_supplier_id'),
        Index('idx_requisition_item_status', 'item_status'),
    )


class RequisitionApproval(Base):
    """
    Approval history for purchase requisitions.
    Tracks the approval workflow and decision history.
    """
    __tablename__ = "requisition_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent requisition
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=False, index=True)
    
    # Approval details
    approval_level = Column(Integer, nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approver_role = Column(String(50), nullable=False)
    
    # Decision
    decision = Column(String(20), nullable=False)  # "approved", "rejected", "returned"
    decision_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Comments and conditions
    comments = Column(Text)
    conditions = Column(Text)  # Conditions for approval
    
    # Financial approval
    approved_amount = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    budget_impact_notes = Column(Text)
    
    # Workflow information
    escalated_from = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Previous approver if escalated
    escalation_reason = Column(Text)
    
    # Delegation information
    delegated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # If approval was delegated
    delegation_reason = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    requisition = relationship("PurchaseRequisition", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])
    escalated_from_user = relationship("User", foreign_keys=[escalated_from])
    delegated_by_user = relationship("User", foreign_keys=[delegated_by])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("decision IN ('approved', 'rejected', 'returned')", name='chk_approval_decision_valid'),
        CheckConstraint("approved_amount IS NULL OR approved_amount >= 0", name='chk_approval_amount_non_negative'),
        Index('idx_requisition_approval_level', 'requisition_id', 'approval_level'),
        Index('idx_requisition_approval_approver', 'approver_id'),
        Index('idx_requisition_approval_date', 'decision_date'),
    )


class RequisitionComment(Base):
    """
    Comments and communications on purchase requisitions.
    Allows stakeholders to communicate during the requisition process.
    """
    __tablename__ = "requisition_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent requisition
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=False, index=True)
    
    # Comment details
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50), default="general")  # "general", "approval", "clarification", "system"
    
    # Author information
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author_role = Column(String(50))
    
    # Visibility and notifications
    is_internal = Column(Boolean, default=True)  # Internal vs. visible to supplier
    is_system_generated = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    
    # Thread and reply structure
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("requisition_comments.id"))
    thread_id = Column(UUID(as_uuid=True), default=uuid.uuid4)  # Groups related comments
    
    # Status and resolution
    requires_response = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    requisition = relationship("PurchaseRequisition", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    parent_comment = relationship("RequisitionComment", remote_side=[id])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("comment_type IN ('general', 'approval', 'clarification', 'system')", 
                       name='chk_comment_type_valid'),
        Index('idx_requisition_comment_author', 'author_id'),
        Index('idx_requisition_comment_created', 'created_at'),
        Index('idx_requisition_comment_thread', 'thread_id'),
        Index('idx_requisition_comment_parent', 'parent_comment_id'),
    )
