"""
Quotation and RFQ (Request for Quotation) Models
Handles supplier quotations and competitive bidding process.
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


class RFQStatus(str, enum.Enum):
    """Enumeration of possible RFQ statuses."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    CLOSED = "closed"
    AWARDED = "awarded"
    CANCELLED = "cancelled"


class QuoteStatus(str, enum.Enum):
    """Enumeration of possible quote statuses."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class RequestForQuotation(Base):
    """
    Request for Quotation (RFQ) model.
    Central entity for managing competitive bidding processes.
    """
    __tablename__ = "requests_for_quotation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    rfq_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Multi-tenant & organization
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, index=True)
    department = Column(String(100))
    cost_center = Column(String(50))
    project_code = Column(String(50))
    
    # Status and workflow
    status = Column(Enum(RFQStatus), default=RFQStatus.DRAFT, nullable=False, index=True)
    
    # Source information
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"))
    
    # RFQ details
    rfq_type = Column(String(50), default="standard")  # "standard", "sealed_bid", "two_stage", "framework"
    bidding_method = Column(String(50), default="competitive")  # "competitive", "negotiated", "single_source"
    
    # Timeline
    issue_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submission_deadline = Column(DateTime(timezone=True), nullable=False)
    quotation_valid_until = Column(DateTime(timezone=True))
    evaluation_completion_date = Column(DateTime(timezone=True))
    award_date = Column(DateTime(timezone=True))
    
    # Requirements
    minimum_suppliers = Column(Integer, default=3)
    maximum_suppliers = Column(Integer)
    pre_qualification_required = Column(Boolean, default=False)
    site_visit_required = Column(Boolean, default=False)
    sample_required = Column(Boolean, default=False)
    
    # Financial information
    estimated_budget = Column(Numeric(15, 2))
    maximum_budget = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    budget_disclosed = Column(Boolean, default=False)  # Whether to disclose budget to suppliers
    
    # Terms and conditions
    payment_terms = Column(String(100))
    delivery_terms = Column(String(100))  # Incoterms
    warranty_requirements = Column(Text)
    service_level_requirements = Column(Text)
    
    # Evaluation criteria
    evaluation_criteria = Column(JSONB)  # Structured evaluation criteria with weights
    price_weight = Column(Numeric(5, 2), default=50.00)  # Percentage weight for price
    technical_weight = Column(Numeric(5, 2), default=30.00)  # Percentage weight for technical
    commercial_weight = Column(Numeric(5, 2), default=20.00)  # Percentage weight for commercial
    
    # Contact information
    contact_person = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    
    # Delivery information
    delivery_address = Column(Text)
    delivery_requirements = Column(Text)
    
    # Document management
    specification_document = Column(String(500))  # Path to specification document
    terms_document = Column(String(500))  # Path to terms and conditions document
    attachments = Column(JSONB)  # Additional document attachments
    
    # Supplier management
    invited_suppliers = Column(JSONB)  # List of specifically invited supplier IDs
    public_rfq = Column(Boolean, default=False)  # Whether open to all suppliers
    
    # Evaluation and award
    evaluation_committee = Column(JSONB)  # List of evaluator user IDs
    evaluation_completed = Column(Boolean, default=False)
    winning_quote_id = Column(UUID(as_uuid=True), ForeignKey("supplier_quotes.id"))
    award_reason = Column(Text)
    
    # Closure
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    closure_reason = Column(Text)
    
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cancellation_reason = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    tags = Column(JSONB)
    custom_fields = Column(JSONB)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    requisition = relationship("PurchaseRequisition")
    contact_person_user = relationship("User", foreign_keys=[contact_person])
    winning_quote = relationship("SupplierQuote", foreign_keys=[winning_quote_id])
    closer = relationship("User", foreign_keys=[closed_by])
    canceller = relationship("User", foreign_keys=[cancelled_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    items = relationship("RFQItem", back_populates="rfq", cascade="all, delete-orphan")
    quotes = relationship("SupplierQuote", back_populates="rfq", cascade="all, delete-orphan", foreign_keys="SupplierQuote.rfq_id")
    evaluations = relationship("QuoteEvaluation", back_populates="rfq", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("submission_deadline > issue_date", name='chk_rfq_deadline_after_issue'),
        CheckConstraint("quotation_valid_until IS NULL OR quotation_valid_until >= submission_deadline", 
                       name='chk_rfq_validity_after_deadline'),
        CheckConstraint("minimum_suppliers >= 1", name='chk_rfq_min_suppliers_positive'),
        CheckConstraint("maximum_suppliers IS NULL OR maximum_suppliers >= minimum_suppliers", 
                       name='chk_rfq_max_suppliers_valid'),
        CheckConstraint("price_weight + technical_weight + commercial_weight = 100", 
                       name='chk_rfq_weights_total_100'),
        CheckConstraint("estimated_budget IS NULL OR estimated_budget >= 0", name='chk_rfq_budget_non_negative'),
        Index('idx_rfq_unit_status', 'unit_id', 'status'),
        Index('idx_rfq_deadline', 'submission_deadline'),
        Index('idx_rfq_issue_date', 'issue_date'),
        Index('idx_rfq_requisition', 'requisition_id'),
    )


class RFQItem(Base):
    """
    Individual items within an RFQ.
    Detailed specifications for items being quoted.
    """
    __tablename__ = "rfq_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent RFQ
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("requests_for_quotation.id"), nullable=False, index=True)
    
    # Item identification
    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    product_code = Column(String(100))
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text)
    
    # Quantity and units
    quantity_required = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    
    # Specifications
    technical_specifications = Column(Text, nullable=False)
    functional_requirements = Column(Text)
    quality_standards = Column(Text)
    performance_criteria = Column(Text)
    
    # Requirements
    brand_preference = Column(String(100))
    model_preference = Column(String(100))
    acceptable_alternatives = Column(Boolean, default=True)
    sample_required = Column(Boolean, default=False)
    
    # Delivery requirements
    delivery_date_required = Column(DateTime(timezone=True))
    delivery_location = Column(String(200))
    special_delivery_requirements = Column(Text)
    
    # Evaluation criteria specific to this item
    evaluation_notes = Column(Text)
    mandatory_requirements = Column(JSONB)  # Must-have requirements
    preferred_requirements = Column(JSONB)  # Nice-to-have requirements
    
    # Reference information
    current_supplier = Column(String(200))
    current_price = Column(Numeric(12, 2))
    market_price_estimate = Column(Numeric(12, 2))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    rfq = relationship("RequestForQuotation", back_populates="items")
    product = relationship("Product")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique line numbers within an RFQ
        Index('idx_rfq_item_line', 'rfq_id', 'line_number', unique=True),
        CheckConstraint("quantity_required > 0", name='chk_rfq_item_quantity_positive'),
        CheckConstraint("current_price IS NULL OR current_price >= 0", name='chk_rfq_item_current_price'),
        CheckConstraint("market_price_estimate IS NULL OR market_price_estimate >= 0", 
                       name='chk_rfq_item_market_price'),
        Index('idx_rfq_item_product', 'product_id'),
        Index('idx_rfq_item_delivery_date', 'delivery_date_required'),
    )


class SupplierQuote(Base):
    """
    Supplier quotations submitted in response to RFQs.
    Contains pricing and technical proposal information.
    """
    __tablename__ = "supplier_quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    quote_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_reference = Column(String(100))  # Supplier's own quote reference
    
    # Parent RFQ and supplier
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("requests_for_quotation.id"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_contact_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contacts.id"))
    
    # Status and workflow
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False, index=True)
    
    # Submission information
    submitted_at = Column(DateTime(timezone=True))
    submitted_by = Column(String(200))  # Name of person who submitted
    submission_method = Column(String(50))  # "email", "portal", "hand_delivery"
    
    # Financial summary
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    shipping_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD")
    
    # Terms and conditions
    validity_period_days = Column(Integer, default=30)
    payment_terms = Column(String(100))
    delivery_terms = Column(String(100))
    warranty_terms = Column(Text)
    
    # Delivery commitment
    delivery_lead_time_days = Column(Integer)
    earliest_delivery_date = Column(DateTime(timezone=True))
    promised_delivery_date = Column(DateTime(timezone=True))
    delivery_commitment = Column(Text)
    
    # Technical proposal
    technical_proposal = Column(Text)
    compliance_statement = Column(Text)
    deviations_from_spec = Column(Text)
    value_added_services = Column(Text)
    
    # Company information
    company_profile = Column(Text)
    relevant_experience = Column(Text)
    certifications = Column(JSONB)
    references = Column(JSONB)  # Customer references
    
    # Document attachments
    technical_documents = Column(JSONB)
    commercial_documents = Column(JSONB)
    certificates = Column(JSONB)
    samples_provided = Column(Boolean, default=False)
    
    # Evaluation results
    evaluated = Column(Boolean, default=False)
    evaluation_score = Column(Numeric(5, 2))  # Overall score
    price_score = Column(Numeric(5, 2))
    technical_score = Column(Numeric(5, 2))
    commercial_score = Column(Numeric(5, 2))
    
    # Decision
    is_winning_quote = Column(Boolean, default=False)
    decision_date = Column(DateTime(timezone=True))
    decision_reason = Column(Text)
    feedback_provided = Column(Text)
    
    # Rejection information
    rejected_at = Column(DateTime(timezone=True))
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    notes = Column(Text)
    tags = Column(JSONB)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    rfq = relationship("RequestForQuotation", back_populates="quotes", foreign_keys=[rfq_id])
    supplier = relationship("Supplier")
    supplier_contact = relationship("SupplierContact")
    rejecter = relationship("User", foreign_keys=[rejected_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    evaluations = relationship("QuoteEvaluation", back_populates="quote", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name='chk_quote_subtotal_non_negative'),
        CheckConstraint("total_amount >= 0", name='chk_quote_total_non_negative'),
        CheckConstraint("tax_amount >= 0", name='chk_quote_tax_non_negative'),
        CheckConstraint("shipping_amount >= 0", name='chk_quote_shipping_non_negative'),
        CheckConstraint("discount_amount >= 0", name='chk_quote_discount_non_negative'),
        CheckConstraint("validity_period_days > 0", name='chk_quote_validity_positive'),
        CheckConstraint("delivery_lead_time_days IS NULL OR delivery_lead_time_days >= 0", 
                       name='chk_quote_lead_time_non_negative'),
        CheckConstraint("evaluation_score IS NULL OR (evaluation_score >= 0 AND evaluation_score <= 100)", 
                       name='chk_quote_evaluation_score_range'),
        Index('idx_quote_rfq_supplier', 'rfq_id', 'supplier_id', unique=True),
        Index('idx_quote_submitted_date', 'submitted_at'),
        Index('idx_quote_decision_date', 'decision_date'),
    )


class QuoteItem(Base):
    """
    Individual items within a supplier quote.
    Line-by-line pricing and specifications.
    """
    __tablename__ = "quote_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent quote and reference to RFQ item
    quote_id = Column(UUID(as_uuid=True), ForeignKey("supplier_quotes.id"), nullable=False, index=True)
    rfq_item_id = Column(UUID(as_uuid=True), ForeignKey("rfq_items.id"), nullable=False, index=True)
    
    # Item identification
    line_number = Column(Integer, nullable=False)
    supplier_part_number = Column(String(100))
    manufacturer = Column(String(100))
    manufacturer_part_number = Column(String(100))
    brand = Column(String(100))
    model = Column(String(100))
    
    # Offered product details
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text)
    technical_specifications = Column(Text)
    
    # Quantity and pricing
    quantity_quoted = Column(Numeric(15, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Discounts and adjustments
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    
    # Delivery information
    delivery_lead_time_days = Column(Integer)
    delivery_date = Column(DateTime(timezone=True))
    delivery_location = Column(String(200))
    
    # Compliance and alternatives
    complies_with_specification = Column(Boolean, default=True)
    deviations = Column(Text)
    alternative_offered = Column(Boolean, default=False)
    alternative_description = Column(Text)
    alternative_justification = Column(Text)
    
    # Warranty and service
    warranty_period_months = Column(Integer)
    warranty_terms = Column(Text)
    service_included = Column(Boolean, default=False)
    service_description = Column(Text)
    
    # Evaluation
    technical_score = Column(Numeric(5, 2))
    commercial_score = Column(Numeric(5, 2))
    price_competitiveness = Column(String(20))  # "very_competitive", "competitive", "average", "high", "very_high"
    evaluator_notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote = relationship("SupplierQuote", back_populates="items")
    rfq_item = relationship("RFQItem")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique line numbers within a quote
        Index('idx_quote_item_line', 'quote_id', 'line_number', unique=True),
        # One quote item per RFQ item per quote
        Index('idx_quote_item_rfq_unique', 'quote_id', 'rfq_item_id', unique=True),
        CheckConstraint("quantity_quoted > 0", name='chk_quote_item_quantity_positive'),
        CheckConstraint("unit_price >= 0", name='chk_quote_item_price_non_negative'),
        CheckConstraint("line_total >= 0", name='chk_quote_item_total_non_negative'),
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 100", 
                       name='chk_quote_item_discount_percentage'),
        CheckConstraint("warranty_period_months IS NULL OR warranty_period_months >= 0", 
                       name='chk_quote_item_warranty_period'),
        CheckConstraint("technical_score IS NULL OR (technical_score >= 0 AND technical_score <= 100)", 
                       name='chk_quote_item_technical_score_range'),
        CheckConstraint("commercial_score IS NULL OR (commercial_score >= 0 AND commercial_score <= 100)", 
                       name='chk_quote_item_commercial_score_range'),
        Index('idx_quote_item_delivery_date', 'delivery_date'),
    )


class QuoteEvaluation(Base):
    """
    Evaluation records for supplier quotes.
    Tracks the evaluation process and scoring.
    """
    __tablename__ = "quote_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("requests_for_quotation.id"), nullable=False, index=True)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("supplier_quotes.id"), nullable=False, index=True)
    
    # Evaluator information
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    evaluator_role = Column(String(50))
    evaluation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Scoring
    price_score = Column(Numeric(5, 2), nullable=False)  # Out of 100
    technical_score = Column(Numeric(5, 2), nullable=False)  # Out of 100
    commercial_score = Column(Numeric(5, 2), nullable=False)  # Out of 100
    overall_score = Column(Numeric(5, 2), nullable=False)  # Weighted average
    
    # Detailed evaluation
    price_evaluation = Column(Text)
    technical_evaluation = Column(Text)
    commercial_evaluation = Column(Text)
    
    # Recommendations
    recommendation = Column(String(50), nullable=False)  # "recommend", "not_recommend", "conditional"
    recommendation_reason = Column(Text)
    conditions = Column(Text)  # If conditional recommendation
    
    # Risk assessment
    risk_assessment = Column(Text)
    risk_level = Column(String(20), default="low")  # "low", "medium", "high"
    risk_mitigation = Column(Text)
    
    # Compliance check
    specification_compliance = Column(Boolean, default=True)
    compliance_notes = Column(Text)
    
    # Additional notes
    strengths = Column(Text)
    weaknesses = Column(Text)
    general_comments = Column(Text)
    
    # Status
    evaluation_status = Column(String(50), default="draft")  # "draft", "submitted", "approved"
    submitted_at = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    rfq = relationship("RequestForQuotation", back_populates="evaluations")
    quote = relationship("SupplierQuote", back_populates="evaluations")
    evaluator = relationship("User", foreign_keys=[evaluator_id])
    approver = relationship("User", foreign_keys=[approved_by])
    
    # Constraints and indexes
    __table_args__ = (
        # One evaluation per evaluator per quote
        Index('idx_quote_evaluation_unique', 'quote_id', 'evaluator_id', unique=True),
        CheckConstraint("price_score >= 0 AND price_score <= 100", name='chk_evaluation_price_score_range'),
        CheckConstraint("technical_score >= 0 AND technical_score <= 100", name='chk_evaluation_technical_score_range'),
        CheckConstraint("commercial_score >= 0 AND commercial_score <= 100", name='chk_evaluation_commercial_score_range'),
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", name='chk_evaluation_overall_score_range'),
        CheckConstraint("recommendation IN ('recommend', 'not_recommend', 'conditional')", 
                       name='chk_evaluation_recommendation_valid'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name='chk_evaluation_risk_level_valid'),
        Index('idx_quote_evaluation_rfq', 'rfq_id'),
        Index('idx_quote_evaluation_evaluator', 'evaluator_id'),
        Index('idx_quote_evaluation_date', 'evaluation_date'),
    )
