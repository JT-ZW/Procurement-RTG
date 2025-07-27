from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base


class Supplier(Base):
    """
    Main supplier model representing companies that provide products to hotel units.
    Suppliers can work with multiple units with different terms and performance.
    """
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic company information
    company_name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(200))  # Official legal name if different
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Business registration
    business_registration_number = Column(String(100))
    tax_id = Column(String(100))
    vat_number = Column(String(100))
    
    # Industry and classification
    industry_type = Column(String(100))  # "Food & Beverage", "Housekeeping", "Maintenance", etc.
    supplier_category = Column(String(100))  # "Local", "National", "International"
    business_type = Column(String(50))  # "Manufacturer", "Distributor", "Service Provider"
    
    # Address information
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Contact information
    primary_phone = Column(String(50))
    secondary_phone = Column(String(50))
    primary_email = Column(String(200))
    website = Column(String(200))
    
    # Business details
    year_established = Column(Integer)
    employee_count = Column(Integer)
    annual_revenue = Column(Numeric(15, 2))
    credit_rating = Column(String(10))  # "AAA", "AA", "A", "BBB", etc.
    
    # Operational information
    delivery_radius_km = Column(Integer)  # Delivery coverage area
    min_order_value = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    payment_terms_default = Column(String(100))  # "Net 30", "Net 15", "COD"
    
    # Capabilities and certifications
    certifications = Column(JSONB)  # ["ISO 9001", "HACCP", "Organic", etc.]
    capabilities = Column(JSONB)  # ["24/7 delivery", "cold chain", "bulk orders", etc.]
    product_categories = Column(JSONB)  # Categories they supply
    
    # Performance summary (calculated fields)
    overall_rating = Column(Numeric(3, 2), default=0.00)  # 1.00 to 5.00
    total_orders = Column(Integer, default=0)
    total_order_value = Column(Numeric(15, 2), default=0.00)
    on_time_delivery_rate = Column(Numeric(5, 2), default=0.00)  # Percentage
    quality_score = Column(Numeric(5, 2), default=0.00)  # Percentage
    
    # Status and lifecycle
    status = Column(String(50), default="active", nullable=False)  # "active", "inactive", "suspended", "blacklisted"
    is_approved = Column(Boolean, default=False)  # Approved for procurement
    is_preferred = Column(Boolean, default=False)  # Preferred supplier status
    risk_level = Column(String(20), default="low")  # "low", "medium", "high"
    
    # Contract and relationship
    primary_contact_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contacts.id"))
    contract_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Internal contract manager
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional information
    notes = Column(Text)
    special_instructions = Column(Text)
    emergency_contact = Column(JSONB)  # Emergency contact information
    
    # Relationships
    contacts = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")
    unit_relationships = relationship("SupplierUnitRelationship", back_populates="supplier", cascade="all, delete-orphan")
    contracts = relationship("SupplierContract", back_populates="supplier", cascade="all, delete-orphan")
    performance_records = relationship("SupplierPerformance", back_populates="supplier", cascade="all, delete-orphan")
    
    # User relationships for audit
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    contract_manager = relationship("User", foreign_keys=[contract_manager_id])

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("overall_rating IS NULL OR (overall_rating >= 1.0 AND overall_rating <= 5.0)", 
                       name='chk_supplier_overall_rating_range'),
        CheckConstraint("on_time_delivery_rate >= 0 AND on_time_delivery_rate <= 100", 
                       name='chk_supplier_delivery_rate_range'),
        CheckConstraint("quality_score >= 0 AND quality_score <= 100", 
                       name='chk_supplier_quality_score_range'),
        CheckConstraint("year_established IS NULL OR year_established > 1800", 
                       name='chk_supplier_year_established'),
        CheckConstraint("employee_count IS NULL OR employee_count >= 0", 
                       name='chk_supplier_employee_count'),
        CheckConstraint("status IN ('active', 'inactive', 'suspended', 'blacklisted')", 
                       name='chk_supplier_status_valid'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", 
                       name='chk_supplier_risk_level_valid'),
        Index('idx_supplier_company_name', 'company_name'),
        Index('idx_supplier_code', 'supplier_code'),
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_approved', 'is_approved'),
        Index('idx_supplier_preferred', 'is_preferred'),
        Index('idx_supplier_deleted', 'is_deleted'),
        Index('idx_supplier_industry', 'industry_type'),
        Index('idx_supplier_category', 'supplier_category'),
        Index('idx_supplier_city', 'city'),
        Index('idx_supplier_country', 'country'),
        Index('idx_supplier_rating', 'overall_rating'),
        Index('idx_supplier_search', 'company_name', 'supplier_code', 'industry_type'),
    )

    @property
    def is_active(self) -> bool:
        """Check if supplier is currently active."""
        return self.status == "active" and not self.is_deleted

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in parts if part])

    def __repr__(self):
        return f"<Supplier(id='{self.id}', name='{self.company_name}', code='{self.supplier_code}')>"


class SupplierContact(Base):
    """
    Contact persons at supplier companies.
    Multiple contacts per supplier for different roles and departments.
    """
    __tablename__ = "supplier_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))  # "Sales Manager", "Account Executive", etc.
    department = Column(String(100))  # "Sales", "Customer Service", "Logistics"
    
    # Contact information
    email = Column(String(200))
    phone = Column(String(50))
    mobile = Column(String(50))
    extension = Column(String(10))
    
    # Role and responsibilities
    role = Column(String(100))  # "Primary Contact", "Technical Support", "Billing", "Emergency"
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Availability
    working_hours = Column(JSONB)  # {"monday": "9-17", "tuesday": "9-17", ...}
    timezone = Column(String(50))
    languages = Column(JSONB)  # ["English", "Spanish", "French"]
    
    # Preferences
    preferred_contact_method = Column(String(50))  # "email", "phone", "mobile"
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="contacts")
    creator = relationship("User")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("preferred_contact_method IN ('email', 'phone', 'mobile')", 
                       name='chk_contact_method_valid'),
        Index('idx_supplier_contact_supplier', 'supplier_id'),
        Index('idx_supplier_contact_name', 'first_name', 'last_name'),
        Index('idx_supplier_contact_email', 'email'),
        Index('idx_supplier_contact_primary', 'is_primary'),
        Index('idx_supplier_contact_active', 'is_active'),
        Index('idx_supplier_contact_role', 'role'),
    )

    @property
    def full_name(self) -> str:
        """Get full name of contact."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<SupplierContact(id='{self.id}', name='{self.full_name}', supplier_id='{self.supplier_id}')>"


class SupplierUnitRelationship(Base):
    """
    Many-to-many relationship between suppliers and hotel units.
    Tracks unit-specific supplier settings, approval status, and performance.
    """
    __tablename__ = "supplier_unit_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Relationship status
    status = Column(String(50), default="active", nullable=False)  # "active", "inactive", "suspended"
    is_approved = Column(Boolean, default=False)  # Approved for this unit
    approval_date = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Unit-specific settings
    credit_limit = Column(Numeric(12, 2))
    payment_terms = Column(String(100))  # Unit-specific payment terms
    delivery_address = Column(Text)  # Special delivery instructions for this unit
    billing_address = Column(Text)  # Unit-specific billing address
    
    # Performance tracking (unit-specific)
    unit_rating = Column(Numeric(3, 2))  # Rating specific to this unit
    total_orders_unit = Column(Integer, default=0)
    total_value_unit = Column(Numeric(15, 2), default=0.00)
    last_order_date = Column(DateTime(timezone=True))
    
    # Delivery and logistics (unit-specific)
    delivery_days = Column(JSONB)  # ["monday", "wednesday", "friday"]
    delivery_time_window = Column(String(50))  # "9:00-11:00"
    lead_time_days = Column(Integer, default=7)
    minimum_order_value = Column(Numeric(10, 2))
    
    # Contact assignments
    primary_contact_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contacts.id"))
    backup_contact_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contacts.id"))
    
    # Unit manager assignments
    unit_contact_person = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Unit's contact person
    procurement_contact = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Procurement contact
    
    # Special terms and conditions
    special_terms = Column(Text)
    discount_terms = Column(JSONB)  # Volume discounts, seasonal discounts, etc.
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="unit_relationships")
    unit = relationship("Unit")
    primary_contact = relationship("SupplierContact", foreign_keys=[primary_contact_id])
    backup_contact = relationship("SupplierContact", foreign_keys=[backup_contact_id])
    approver = relationship("User", foreign_keys=[approved_by])
    unit_contact = relationship("User", foreign_keys=[unit_contact_person])
    procurement_manager = relationship("User", foreign_keys=[procurement_contact])
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one relationship per supplier per unit
        Index('idx_supplier_unit_unique', 'supplier_id', 'unit_id', unique=True),
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", 
                       name='chk_supplier_unit_status_valid'),
        CheckConstraint("unit_rating IS NULL OR (unit_rating >= 1.0 AND unit_rating <= 5.0)", 
                       name='chk_supplier_unit_rating_range'),
        CheckConstraint("credit_limit IS NULL OR credit_limit >= 0", 
                       name='chk_supplier_unit_credit_limit'),
        CheckConstraint("total_orders_unit >= 0", 
                       name='chk_supplier_unit_orders_non_negative'),
        CheckConstraint("total_value_unit >= 0", 
                       name='chk_supplier_unit_value_non_negative'),
        CheckConstraint("lead_time_days >= 0", 
                       name='chk_supplier_unit_lead_time'),
        Index('idx_supplier_unit_supplier', 'supplier_id'),
        Index('idx_supplier_unit_unit', 'unit_id'),
        Index('idx_supplier_unit_status', 'status'),
        Index('idx_supplier_unit_approved', 'is_approved'),
        Index('idx_supplier_unit_rating', 'unit_rating'),
        Index('idx_supplier_unit_last_order', 'last_order_date'),
    )

    @property
    def is_active_relationship(self) -> bool:
        """Check if supplier-unit relationship is active."""
        return self.status == "active" and self.is_approved

    def __repr__(self):
        return f"<SupplierUnitRelationship(supplier_id='{self.supplier_id}', unit_id='{self.unit_id}', status='{self.status}')>"


class SupplierContract(Base):
    """
    Contracts between suppliers and the hotel group or specific units.
    Manages contract terms, renewal dates, and performance obligations.
    """
    __tablename__ = "supplier_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)  # Null for group-wide contracts
    
    # Contract identification
    contract_number = Column(String(100), unique=True, nullable=False, index=True)
    contract_name = Column(String(200), nullable=False)
    contract_type = Column(String(50), nullable=False)  # "Master Agreement", "Unit Contract", "Service Agreement"
    
    # Contract periods
    effective_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    notice_period_days = Column(Integer, default=30)  # Days notice required for termination
    
    # Contract terms
    total_value = Column(Numeric(15, 2))  # Total contract value if applicable
    currency = Column(String(3), default="USD")
    payment_terms = Column(String(200))
    delivery_terms = Column(String(200))
    
    # Performance requirements
    service_level_requirements = Column(JSONB)  # SLA requirements
    quality_standards = Column(JSONB)  # Quality requirements
    delivery_requirements = Column(JSONB)  # Delivery time requirements
    
    # Pricing and discounts
    pricing_structure = Column(JSONB)  # Volume discounts, tier pricing, etc.
    automatic_renewal = Column(Boolean, default=False)
    renewal_terms = Column(Text)
    
    # Legal and compliance
    governing_law = Column(String(100))
    dispute_resolution = Column(String(200))
    insurance_requirements = Column(JSONB)
    compliance_requirements = Column(JSONB)
    
    # Status and management
    status = Column(String(50), default="draft", nullable=False)  # "draft", "active", "expired", "terminated"
    signed_date = Column(DateTime(timezone=True))
    signed_by_supplier = Column(String(200))  # Signatory name
    signed_by_company = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Internal signatory
    
    # Renewal and notifications
    renewal_reminder_sent = Column(Boolean, default=False)
    renewal_reminder_date = Column(DateTime(timezone=True))
    auto_renewal_enabled = Column(Boolean, default=False)
    
    # Document management
    contract_document_path = Column(String(500))  # Path to contract document
    amendments = Column(JSONB)  # List of amendments with dates and descriptions
    
    # Performance tracking
    performance_score = Column(Numeric(5, 2))  # Overall contract performance score
    penalties_applied = Column(Numeric(12, 2), default=0.00)
    bonuses_awarded = Column(Numeric(12, 2), default=0.00)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional terms
    termination_clauses = Column(Text)
    special_conditions = Column(Text)
    notes = Column(Text)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="contracts")
    unit = relationship("Unit")
    company_signatory = relationship("User", foreign_keys=[signed_by_company])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("effective_date < expiry_date", 
                       name='chk_contract_dates_valid'),
        CheckConstraint("notice_period_days >= 0", 
                       name='chk_contract_notice_period'),
        CheckConstraint("status IN ('draft', 'active', 'expired', 'terminated', 'suspended')", 
                       name='chk_contract_status_valid'),
        CheckConstraint("contract_type IN ('Master Agreement', 'Unit Contract', 'Service Agreement', 'Purchase Agreement')", 
                       name='chk_contract_type_valid'),
        CheckConstraint("total_value IS NULL OR total_value >= 0", 
                       name='chk_contract_value_non_negative'),
        Index('idx_supplier_contract_supplier', 'supplier_id'),
        Index('idx_supplier_contract_unit', 'unit_id'),
        Index('idx_supplier_contract_number', 'contract_number'),
        Index('idx_supplier_contract_status', 'status'),
        Index('idx_supplier_contract_effective', 'effective_date'),
        Index('idx_supplier_contract_expiry', 'expiry_date'),
        Index('idx_supplier_contract_type', 'contract_type'),
        Index('idx_supplier_contract_renewal', 'auto_renewal_enabled', 'expiry_date'),
    )

    @property
    def is_active(self) -> bool:
        """Check if contract is currently active."""
        now = datetime.utcnow()
        return (self.status == "active" and 
                self.effective_date <= now <= self.expiry_date)

    @property
    def days_until_expiry(self) -> int:
        """Get number of days until contract expires."""
        if self.expiry_date:
            delta = self.expiry_date - datetime.utcnow()
            return max(0, delta.days)
        return 0

    @property
    def needs_renewal_attention(self) -> bool:
        """Check if contract needs renewal attention."""
        days_until_expiry = self.days_until_expiry
        return (self.status == "active" and 
                days_until_expiry <= (self.notice_period_days + 30))

    def __repr__(self):
        return f"<SupplierContract(id='{self.id}', number='{self.contract_number}', supplier_id='{self.supplier_id}')>"


class SupplierPerformance(Base):
    """
    Track supplier performance metrics over time.
    Records monthly/quarterly performance data for analysis and reporting.
    """
    __tablename__ = "supplier_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)  # Null for overall performance
    contract_id = Column(UUID(as_uuid=True), ForeignKey("supplier_contracts.id"), nullable=True)
    
    # Performance period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # "monthly", "quarterly", "yearly"
    
    # Order and delivery metrics
    total_orders = Column(Integer, default=0)
    total_order_value = Column(Numeric(15, 2), default=0.00)
    orders_delivered_on_time = Column(Integer, default=0)
    orders_delivered_late = Column(Integer, default=0)
    average_delivery_time_days = Column(Numeric(5, 2))
    
    # Quality metrics
    quality_issues_reported = Column(Integer, default=0)
    quality_issues_resolved = Column(Integer, default=0)
    product_returns = Column(Integer, default=0)
    return_value = Column(Numeric(12, 2), default=0.00)
    
    # Service metrics
    response_time_hours = Column(Numeric(6, 2))  # Average response time to inquiries
    complaint_count = Column(Integer, default=0)
    complaints_resolved = Column(Integer, default=0)
    service_interruptions = Column(Integer, default=0)
    
    # Financial metrics
    invoice_accuracy_rate = Column(Numeric(5, 2))  # Percentage
    payment_discrepancies = Column(Integer, default=0)
    cost_savings_achieved = Column(Numeric(12, 2), default=0.00)
    
    # Calculated scores (0-100)
    delivery_score = Column(Numeric(5, 2))
    quality_score = Column(Numeric(5, 2))
    service_score = Column(Numeric(5, 2))
    overall_score = Column(Numeric(5, 2))
    
    # Comparative metrics
    market_competitiveness = Column(Numeric(5, 2))  # Price competitiveness score
    innovation_score = Column(Numeric(5, 2))  # New products/services introduced
    sustainability_score = Column(Numeric(5, 2))  # Environmental/social responsibility
    
    # Risk assessment
    risk_incidents = Column(Integer, default=0)
    risk_level = Column(String(20))  # "low", "medium", "high"
    compliance_issues = Column(Integer, default=0)
    
    # Improvement tracking
    improvement_areas = Column(JSONB)  # Areas identified for improvement
    action_items = Column(JSONB)  # Action items agreed with supplier
    progress_notes = Column(Text)
    
    # Review information
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    review_date = Column(DateTime(timezone=True))
    next_review_date = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="performance_records")
    unit = relationship("Unit")
    contract = relationship("SupplierContract")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("period_start < period_end", 
                       name='chk_performance_period_valid'),
        CheckConstraint("period_type IN ('monthly', 'quarterly', 'yearly')", 
                       name='chk_performance_period_type_valid'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", 
                       name='chk_performance_risk_level_valid'),
        CheckConstraint("delivery_score IS NULL OR (delivery_score >= 0 AND delivery_score <= 100)", 
                       name='chk_performance_delivery_score_range'),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)", 
                       name='chk_performance_quality_score_range'),
        CheckConstraint("service_score IS NULL OR (service_score >= 0 AND service_score <= 100)", 
                       name='chk_performance_service_score_range'),
        CheckConstraint("overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)", 
                       name='chk_performance_overall_score_range'),
        CheckConstraint("total_orders >= 0", 
                       name='chk_performance_orders_non_negative'),
        CheckConstraint("orders_delivered_on_time + orders_delivered_late <= total_orders", 
                       name='chk_performance_delivery_consistency'),
        Index('idx_supplier_performance_supplier', 'supplier_id'),
        Index('idx_supplier_performance_unit', 'unit_id'),
        Index('idx_supplier_performance_contract', 'contract_id'),
        Index('idx_supplier_performance_period', 'period_start', 'period_end'),
        Index('idx_supplier_performance_type', 'period_type'),
        Index('idx_supplier_performance_overall_score', 'overall_score'),
        Index('idx_supplier_performance_risk', 'risk_level'),
        Index('idx_supplier_performance_review', 'next_review_date'),
        # Unique constraint for performance period per supplier-unit combination
        Index('idx_supplier_performance_unique', 'supplier_id', 'unit_id', 'period_start', 'period_end', unique=True),
    )

    @property
    def on_time_delivery_rate(self) -> float:
        """Calculate on-time delivery rate as percentage."""
        if self.total_orders == 0:
            return 0.0
        return (self.orders_delivered_on_time / self.total_orders) * 100

    @property
    def quality_issue_rate(self) -> float:
        """Calculate quality issue rate as percentage."""
        if self.total_orders == 0:
            return 0.0
        return (self.quality_issues_reported / self.total_orders) * 100

    def __repr__(self):
        return f"<SupplierPerformance(supplier_id='{self.supplier_id}', period='{self.period_start}' to '{self.period_end}')>"