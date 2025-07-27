"""
Invoice and Payment Models
Handles invoice processing and payment management.
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


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    CREDIT_NOTE_ISSUED = "credit_note_issued"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    ELECTRONIC_PAYMENT = "electronic_payment"
    ACH = "ach"
    WIRE_TRANSFER = "wire_transfer"


class Invoice(Base):
    """
    Invoice model for managing supplier invoices.
    Central document for payment processing.
    """
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Invoice identification
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_invoice_number = Column(String(100), nullable=False, index=True)
    invoice_type = Column(String(50), default="standard")  # "standard", "credit_note", "debit_note", "pro_forma"
    
    # Multi-tenant & organization
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, index=True)
    department = Column(String(100))
    cost_center = Column(String(50), index=True)
    
    # Source references
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    purchase_order_number = Column(String(100))
    delivery_receipt_number = Column(String(100))
    contract_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contracts.id"))
    
    # Supplier information
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_contact_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contacts.id"))
    
    # Financial details
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    shipping_amount = Column(Numeric(15, 2), default=0)
    other_charges = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Exchange rate (for multi-currency)
    exchange_rate = Column(Numeric(12, 6))
    base_currency = Column(String(3))
    base_amount = Column(Numeric(15, 2))
    
    # Dates
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    received_date = Column(DateTime(timezone=True), server_default=func.now())
    service_period_start = Column(DateTime(timezone=True))
    service_period_end = Column(DateTime(timezone=True))
    
    # Status and workflow
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.RECEIVED, nullable=False, index=True)
    
    # Payment terms
    payment_terms = Column(String(100))
    early_payment_discount_percentage = Column(Numeric(5, 2))
    early_payment_discount_days = Column(Integer)
    late_payment_penalty_percentage = Column(Numeric(5, 2))
    
    # Approval workflow
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Rejection details
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejected_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # Three-way matching
    po_matching_status = Column(String(50))  # "matched", "variance", "no_po"
    receipt_matching_status = Column(String(50))  # "matched", "variance", "no_receipt"
    price_variance_amount = Column(Numeric(15, 2))
    quantity_variance = Column(Numeric(15, 3))
    matching_notes = Column(Text)
    
    # Document management
    document_path = Column(String(500))  # Path to invoice document
    attachments = Column(JSONB)  # Additional attachments
    
    # Processing information
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    processed_at = Column(DateTime(timezone=True))
    processing_notes = Column(Text)
    
    # Payment information
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    payment_due_amount = Column(Numeric(15, 2))
    payment_completed_amount = Column(Numeric(15, 2), default=0)
    payment_pending_amount = Column(Numeric(15, 2))
    
    # Dispute management
    is_disputed = Column(Boolean, default=False, index=True)
    dispute_raised_at = Column(DateTime(timezone=True))
    dispute_raised_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    dispute_reason = Column(Text)
    dispute_amount = Column(Numeric(15, 2))
    dispute_resolved_at = Column(DateTime(timezone=True))
    
    # Accounting integration
    gl_posted = Column(Boolean, default=False)
    gl_posting_date = Column(DateTime(timezone=True))
    gl_document_number = Column(String(100))
    accounting_period = Column(String(20))
    
    # Vendor performance impact
    payment_performance_rating = Column(Numeric(3, 2))  # Impact on supplier rating
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    tags = Column(JSONB)
    custom_fields = Column(JSONB)
    notes = Column(Text)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    purchase_order = relationship("PurchaseOrder")
    contract = relationship("SupplierContract")
    supplier = relationship("Supplier")
    supplier_contact = relationship("SupplierContact")
    approver = relationship("User", foreign_keys=[approved_by])
    rejecter = relationship("User", foreign_keys=[rejected_by])
    processor = relationship("User", foreign_keys=[processed_by])
    dispute_raiser = relationship("User", foreign_keys=[dispute_raised_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    status_history = relationship("InvoiceStatusHistory", back_populates="invoice", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name='chk_invoice_subtotal_non_negative'),
        CheckConstraint("total_amount >= 0", name='chk_invoice_total_non_negative'),
        CheckConstraint("tax_amount >= 0", name='chk_invoice_tax_non_negative'),
        CheckConstraint("discount_amount >= 0", name='chk_invoice_discount_non_negative'),
        CheckConstraint("shipping_amount >= 0", name='chk_invoice_shipping_non_negative'),
        CheckConstraint("other_charges >= 0", name='chk_invoice_other_charges_non_negative'),
        CheckConstraint("exchange_rate IS NULL OR exchange_rate > 0", name='chk_invoice_exchange_rate_positive'),
        CheckConstraint("due_date >= invoice_date", name='chk_invoice_due_date_valid'),
        CheckConstraint("early_payment_discount_percentage IS NULL OR (early_payment_discount_percentage >= 0 AND early_payment_discount_percentage <= 100)", 
                       name='chk_invoice_early_discount_range'),
        CheckConstraint("late_payment_penalty_percentage IS NULL OR (late_payment_penalty_percentage >= 0 AND late_payment_penalty_percentage <= 100)", 
                       name='chk_invoice_late_penalty_range'),
        CheckConstraint("payment_completed_amount >= 0", name='chk_invoice_payment_completed_non_negative'),
        CheckConstraint("dispute_amount IS NULL OR dispute_amount >= 0", name='chk_invoice_dispute_amount_non_negative'),
        Index('idx_invoice_unit_status', 'unit_id', 'status'),
        Index('idx_invoice_supplier', 'supplier_id'),
        Index('idx_invoice_po', 'purchase_order_id'),
        Index('idx_invoice_dates', 'invoice_date', 'due_date'),
        Index('idx_invoice_payment_status', 'payment_status'),
        Index('idx_invoice_supplier_number', 'supplier_id', 'supplier_invoice_number'),
    )


class InvoiceLineItem(Base):
    """
    Individual line items within an invoice.
    Detailed breakdown of invoice charges.
    """
    __tablename__ = "invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent invoice
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Line item details
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    
    # Product reference
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    product_code = Column(String(100))
    supplier_part_number = Column(String(100))
    
    # Purchase order reference
    po_line_item_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_items.id"))
    
    # Quantity and pricing
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(50))
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Tax and discounts
    tax_percentage = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    
    # Service period (for service items)
    service_period_start = Column(DateTime(timezone=True))
    service_period_end = Column(DateTime(timezone=True))
    
    # Matching information
    po_matched = Column(Boolean, default=False)
    receipt_matched = Column(Boolean, default=False)
    price_variance = Column(Numeric(12, 2))
    quantity_variance = Column(Numeric(15, 3))
    
    # Accounting
    account_code = Column(String(50))
    cost_center = Column(String(50))
    project_code = Column(String(50))
    asset_category = Column(String(50))
    
    # Notes
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    product = relationship("Product")
    po_line_item = relationship("PurchaseOrderItem")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique line numbers within invoice
        Index('idx_invoice_line_number', 'invoice_id', 'line_number', unique=True),
        CheckConstraint("quantity > 0", name='chk_invoice_line_quantity_positive'),
        CheckConstraint("unit_price >= 0", name='chk_invoice_line_price_non_negative'),
        CheckConstraint("line_total >= 0", name='chk_invoice_line_total_non_negative'),
        CheckConstraint("tax_percentage >= 0 AND tax_percentage <= 100", name='chk_invoice_line_tax_percentage'),
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 100", name='chk_invoice_line_discount_percentage'),
        Index('idx_invoice_line_product', 'product_id'),
        Index('idx_invoice_line_po', 'po_line_item_id'),
    )


class Payment(Base):
    """
    Payment records for invoices.
    Tracks all payments made against invoices.
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Payment identification
    payment_number = Column(String(100), unique=True, nullable=False, index=True)
    payment_reference = Column(String(100))  # Bank reference, check number, etc.
    
    # Invoice reference
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Payment details
    payment_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(12, 6))
    base_amount = Column(Numeric(15, 2))  # Amount in company's base currency
    
    # Payment method and details
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_account = Column(String(100))  # Bank account, credit card, etc.
    
    # Bank/Financial institution details
    bank_name = Column(String(200))
    bank_account_number = Column(String(100))
    routing_number = Column(String(50))
    swift_code = Column(String(20))
    
    # Check details (if applicable)
    check_number = Column(String(50))
    check_date = Column(DateTime(timezone=True))
    
    # Electronic payment details
    transaction_id = Column(String(100))
    authorization_code = Column(String(50))
    
    # Dates
    payment_date = Column(DateTime(timezone=True), nullable=False)
    value_date = Column(DateTime(timezone=True))  # When funds are available
    scheduled_date = Column(DateTime(timezone=True))  # For scheduled payments
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    # Processing information
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    processed_at = Column(DateTime(timezone=True))
    processing_notes = Column(Text)
    
    # Approval (for high-value payments)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Discount information
    early_payment_discount_taken = Column(Numeric(12, 2), default=0)
    discount_percentage = Column(Numeric(5, 2))
    
    # Withholding and deductions
    withholding_tax_amount = Column(Numeric(12, 2), default=0)
    other_deductions = Column(Numeric(12, 2), default=0)
    net_payment_amount = Column(Numeric(15, 2))
    
    # Failure information
    failure_reason = Column(Text)
    failed_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True))
    
    # Reconciliation
    bank_statement_date = Column(DateTime(timezone=True))
    bank_reference = Column(String(100))
    reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime(timezone=True))
    reconciled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Accounting integration
    gl_posted = Column(Boolean, default=False)
    gl_posting_date = Column(DateTime(timezone=True))
    gl_document_number = Column(String(100))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional information
    notes = Column(Text)
    attachments = Column(JSONB)  # Supporting documents
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    processor = relationship("User", foreign_keys=[processed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    reconciler = relationship("User", foreign_keys=[reconciled_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("payment_amount > 0", name='chk_payment_amount_positive'),
        CheckConstraint("exchange_rate IS NULL OR exchange_rate > 0", name='chk_payment_exchange_rate_positive'),
        CheckConstraint("early_payment_discount_taken >= 0", name='chk_payment_discount_non_negative'),
        CheckConstraint("withholding_tax_amount >= 0", name='chk_payment_withholding_non_negative'),
        CheckConstraint("other_deductions >= 0", name='chk_payment_deductions_non_negative'),
        CheckConstraint("net_payment_amount IS NULL OR net_payment_amount >= 0", name='chk_payment_net_amount_non_negative'),
        CheckConstraint("retry_count >= 0", name='chk_payment_retry_count_non_negative'),
        CheckConstraint("discount_percentage IS NULL OR (discount_percentage >= 0 AND discount_percentage <= 100)", 
                       name='chk_payment_discount_percentage_range'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_reference', 'payment_reference'),
        Index('idx_payment_status_date', 'status', 'payment_date'),
    )


class InvoiceStatusHistory(Base):
    """
    Status change history for invoices.
    Audit trail of all status transitions.
    """
    __tablename__ = "invoice_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent invoice
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Status change details
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
    related_document_type = Column(String(50))  # "payment", "approval", "dispute"
    related_document_id = Column(UUID(as_uuid=True))
    
    # Relationships
    invoice = relationship("Invoice", back_populates="status_history")
    changed_by_user = relationship("User")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_invoice_status_history_invoice', 'invoice_id'),
        Index('idx_invoice_status_history_date', 'changed_at'),
        Index('idx_invoice_status_history_user', 'changed_by'),
    )
