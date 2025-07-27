"""
Purchase Order Models
Handles formal purchase orders generated from approved requisitions.
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


class PurchaseOrderStatus(str, enum.Enum):
    """Enumeration of possible purchase order statuses."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT_TO_SUPPLIER = "sent_to_supplier"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    PAID = "paid"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class PurchaseOrderType(str, enum.Enum):
    """Types of purchase orders."""
    STANDARD = "standard"
    BLANKET = "blanket"
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"
    SERVICE = "service"
    CAPITAL = "capital"


class PurchaseOrder(Base):
    """
    Main purchase order model.
    Formal document sent to suppliers for procurement.
    """
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    po_type = Column(Enum(PurchaseOrderType), default=PurchaseOrderType.STANDARD, nullable=False)
    title = Column(String(200))
    description = Column(Text)
    
    # Multi-tenant & organization
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, index=True)
    department = Column(String(100))
    cost_center = Column(String(50), index=True)
    project_code = Column(String(50))
    
    # Status and workflow
    status = Column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, nullable=False, index=True)
    priority = Column(String(20), default="medium")  # "low", "medium", "high", "urgent", "emergency"
    
    # Source information
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"))
    quote_id = Column(UUID(as_uuid=True), ForeignKey("supplier_quotes.id"))  # Reference to winning quote
    
    # Supplier information
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_contact_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contacts.id"))
    supplier_reference = Column(String(100))  # Supplier's own reference number
    
    # Financial information
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    shipping_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD")
    
    # Exchange rate information (for multi-currency)
    exchange_rate = Column(Numeric(12, 6))
    base_currency = Column(String(3))
    
    # Payment terms
    payment_terms = Column(String(100))  # "Net 30", "COD", etc.
    payment_method = Column(String(50))  # "Bank Transfer", "Check", "Credit Card"
    payment_due_date = Column(DateTime(timezone=True))
    early_payment_discount = Column(Numeric(5, 2))  # Percentage
    early_payment_days = Column(Integer)
    
    # Delivery information
    delivery_address = Column(Text, nullable=False)
    delivery_contact_name = Column(String(100))
    delivery_contact_phone = Column(String(50))
    delivery_contact_email = Column(String(200))
    delivery_instructions = Column(Text)
    
    # Dates and scheduling
    order_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    requested_delivery_date = Column(DateTime(timezone=True))
    promised_delivery_date = Column(DateTime(timezone=True))
    actual_delivery_date = Column(DateTime(timezone=True))
    
    # Document management
    document_path = Column(String(500))  # Path to generated PO document
    terms_and_conditions = Column(Text)
    special_instructions = Column(Text)
    
    # Approvals
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Supplier communication
    sent_to_supplier_at = Column(DateTime(timezone=True))
    sent_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    supplier_acknowledged_at = Column(DateTime(timezone=True))
    supplier_acknowledgment_method = Column(String(50))  # "email", "phone", "portal"
    
    # Performance tracking
    days_to_acknowledge = Column(Integer)  # Supplier response time
    days_to_deliver = Column(Integer)  # Actual delivery time
    delivery_performance = Column(String(20))  # "early", "on_time", "late"
    
    # Receiving information
    received_at = Column(DateTime(timezone=True))
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    receiving_notes = Column(Text)
    
    # Invoice information
    invoiced_at = Column(DateTime(timezone=True))
    invoice_number = Column(String(100))
    invoice_amount = Column(Numeric(15, 2))
    payment_status = Column(String(50), default="pending")  # "pending", "paid", "overdue", "disputed"
    
    # Closure and cancellation
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    closure_reason = Column(String(100))  # "completed", "cancelled", "superseded"
    
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cancellation_reason = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    tags = Column(JSONB)  # For categorization
    custom_fields = Column(JSONB)  # Unit-specific custom fields
    attachments = Column(JSONB)  # File attachments metadata
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    requisition = relationship("PurchaseRequisition")
    supplier = relationship("Supplier")
    supplier_contact = relationship("SupplierContact")
    approver = relationship("User", foreign_keys=[approved_by])
    sender = relationship("User", foreign_keys=[sent_by])
    receiver = relationship("User", foreign_keys=[received_by])
    closer = relationship("User", foreign_keys=[closed_by])
    canceller = relationship("User", foreign_keys=[cancelled_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    status_history = relationship("PurchaseOrderStatusHistory", back_populates="purchase_order", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name='chk_po_subtotal_non_negative'),
        CheckConstraint("total_amount >= 0", name='chk_po_total_non_negative'),
        CheckConstraint("tax_amount >= 0", name='chk_po_tax_non_negative'),
        CheckConstraint("shipping_amount >= 0", name='chk_po_shipping_non_negative'),
        CheckConstraint("discount_amount >= 0", name='chk_po_discount_non_negative'),
        CheckConstraint("exchange_rate IS NULL OR exchange_rate > 0", name='chk_po_exchange_rate_positive'),
        CheckConstraint("early_payment_discount IS NULL OR (early_payment_discount >= 0 AND early_payment_discount <= 100)", 
                       name='chk_po_early_payment_discount_range'),
        Index('idx_po_unit_status', 'unit_id', 'status'),
        Index('idx_po_supplier', 'supplier_id'),
        Index('idx_po_order_date', 'order_date'),
        Index('idx_po_delivery_date', 'requested_delivery_date'),
        Index('idx_po_requisition', 'requisition_id'),
        Index('idx_po_cost_center', 'cost_center'),
    )


class PurchaseOrderItem(Base):
    """
    Individual items within a purchase order.
    Line items with detailed specifications and pricing.
    """
    __tablename__ = "purchase_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent purchase order
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    
    # Item identification
    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    product_code = Column(String(100))
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text)
    
    # Supplier information
    supplier_part_number = Column(String(100))
    supplier_description = Column(Text)
    manufacturer = Column(String(100))
    manufacturer_part_number = Column(String(100))
    
    # Quantity and units
    quantity_ordered = Column(Numeric(15, 3), nullable=False)
    quantity_received = Column(Numeric(15, 3), default=0)
    quantity_invoiced = Column(Numeric(15, 3), default=0)
    unit_of_measure = Column(String(50), nullable=False)
    
    # Pricing
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Discounts and charges
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_percentage = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    
    # Delivery information
    requested_delivery_date = Column(DateTime(timezone=True))
    promised_delivery_date = Column(DateTime(timezone=True))
    actual_delivery_date = Column(DateTime(timezone=True))
    delivery_location = Column(String(200))
    
    # Specifications and requirements
    technical_specifications = Column(Text)
    quality_requirements = Column(Text)
    inspection_requirements = Column(Text)
    
    # Status tracking
    item_status = Column(String(50), default="ordered")  # "ordered", "acknowledged", "shipped", "received", "inspected", "accepted", "rejected"
    receipt_status = Column(String(50), default="pending")  # "pending", "partial", "complete", "over_received"
    
    # Quality and inspection
    inspection_required = Column(Boolean, default=True)
    inspection_passed = Column(Boolean)
    inspection_date = Column(DateTime(timezone=True))
    inspection_notes = Column(Text)
    quality_rating = Column(Numeric(3, 2))  # 1.00 to 5.00
    
    # Accounting
    account_code = Column(String(50))
    cost_center = Column(String(50))
    project_code = Column(String(50))
    asset_category = Column(String(50))  # For capital items
    
    # Notes and comments
    notes = Column(Text)
    receiving_notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique line numbers within a purchase order
        Index('idx_po_item_line', 'purchase_order_id', 'line_number', unique=True),
        CheckConstraint("quantity_ordered > 0", name='chk_po_item_quantity_positive'),
        CheckConstraint("quantity_received >= 0", name='chk_po_item_received_quantity'),
        CheckConstraint("quantity_invoiced >= 0", name='chk_po_item_invoiced_quantity'),
        CheckConstraint("unit_price >= 0", name='chk_po_item_price_non_negative'),
        CheckConstraint("line_total >= 0", name='chk_po_item_total_non_negative'),
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 100", name='chk_po_item_discount_percentage'),
        CheckConstraint("tax_percentage >= 0 AND tax_percentage <= 100", name='chk_po_item_tax_percentage'),
        CheckConstraint("quality_rating IS NULL OR (quality_rating >= 1.0 AND quality_rating <= 5.0)", 
                       name='chk_po_item_quality_rating_range'),
        Index('idx_po_item_product', 'product_id'),
        Index('idx_po_item_status', 'item_status'),
        Index('idx_po_item_delivery_date', 'requested_delivery_date'),
    )


class PurchaseOrderStatusHistory(Base):
    """
    Status change history for purchase orders.
    Tracks all status transitions with timestamps and reasons.
    """
    __tablename__ = "purchase_order_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent purchase order
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    
    # Status change information
    from_status = Column(String(50))
    to_status = Column(String(50), nullable=False)
    change_reason = Column(Text)
    change_notes = Column(Text)
    
    # Who made the change
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # System or manual change
    is_system_change = Column(Boolean, default=False)
    trigger_event = Column(String(100))  # What triggered the change
    
    # Additional context
    related_document_type = Column(String(50))  # "receipt", "invoice", "approval"
    related_document_id = Column(UUID(as_uuid=True))
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="status_history")
    changed_by_user = relationship("User")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_po_status_history_po', 'purchase_order_id'),
        Index('idx_po_status_history_date', 'changed_at'),
        Index('idx_po_status_history_user', 'changed_by'),
    )
