from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from decimal import Decimal

from app.core.database import Base


class Unit(Base):
    """
    Main hotel unit model representing individual hotel properties.
    Core of the multi-tenant architecture - all other entities relate to units.
    """
    __tablename__ = "units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic unit information
    name = Column(String(200), nullable=False, index=True)
    unit_code = Column(String(50), unique=True, nullable=False, index=True)  # Unique identifier like "HTL001"
    display_name = Column(String(200))  # Display name for UI
    
    # Property details
    property_type = Column(String(100))  # "Hotel", "Resort", "Conference Center", "Restaurant"
    brand = Column(String(100))  # Hotel brand if applicable
    star_rating = Column(Integer)  # 1-5 star rating
    room_count = Column(Integer)
    
    # Location information
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100), index=True)
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), index=True)
    
    # Geographic coordinates
    latitude = Column(Numeric(10, 8))  # For mapping and logistics
    longitude = Column(Numeric(11, 8))
    timezone = Column(String(50), default="UTC")
    
    # Contact information
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(200))
    website = Column(String(200))
    
    # Operational information
    opening_date = Column(DateTime(timezone=True))
    renovation_date = Column(DateTime(timezone=True))
    license_number = Column(String(100))  # Business license
    tax_id = Column(String(100))  # Local tax identification
    
    # Management structure
    general_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    procurement_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    finance_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Operational settings
    currency = Column(String(3), default="USD")
    language = Column(String(10), default="en")
    business_hours = Column(JSONB)  # {"monday": "24/7", "tuesday": "24/7", ...}
    seasonal_closure = Column(JSONB)  # Seasonal closure dates if applicable
    
    # Capacity and specifications
    employee_count = Column(Integer)
    guest_capacity = Column(Integer)
    meeting_rooms = Column(Integer)
    restaurants = Column(Integer)
    parking_spaces = Column(Integer)
    
    # Financial information
    annual_revenue = Column(Numeric(15, 2))
    annual_procurement_budget = Column(Numeric(12, 2))
    cost_center_code = Column(String(50))
    profit_center_code = Column(String(50))
    
    # Certifications and compliance
    certifications = Column(JSONB)  # ["ISO 9001", "Green Hotel", "HACCP", etc.]
    compliance_requirements = Column(JSONB)  # Regulatory requirements
    insurance_info = Column(JSONB)  # Insurance details
    
    # Status and lifecycle
    status = Column(String(50), default="active", nullable=False)  # "active", "inactive", "under_renovation", "closed"
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
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
    description = Column(Text)
    amenities = Column(JSONB)  # List of amenities
    special_features = Column(JSONB)  # Special features or services
    notes = Column(Text)  # Internal notes
    
    # Relationships
    config = relationship("UnitConfig", back_populates="unit", uselist=False, cascade="all, delete-orphan")
    budgets = relationship("UnitBudget", back_populates="unit", cascade="all, delete-orphan")
    user_assignments = relationship("UserUnitAssignment", cascade="all, delete-orphan")
    
    # Manager relationships
    general_manager = relationship("User", foreign_keys=[general_manager_id])
    procurement_manager = relationship("User", foreign_keys=[procurement_manager_id])
    finance_manager = relationship("User", foreign_keys=[finance_manager_id])
    
    # Audit relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'under_renovation', 'closed', 'planning')", 
                       name='chk_unit_status_valid'),
        CheckConstraint("star_rating IS NULL OR (star_rating >= 1 AND star_rating <= 5)", 
                       name='chk_unit_star_rating_range'),
        CheckConstraint("room_count IS NULL OR room_count >= 0", 
                       name='chk_unit_room_count_non_negative'),
        CheckConstraint("employee_count IS NULL OR employee_count >= 0", 
                       name='chk_unit_employee_count_non_negative'),
        CheckConstraint("guest_capacity IS NULL OR guest_capacity >= 0", 
                       name='chk_unit_guest_capacity_non_negative'),
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", 
                       name='chk_unit_latitude_range'),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", 
                       name='chk_unit_longitude_range'),
        Index('idx_unit_name', 'name'),
        Index('idx_unit_code', 'unit_code'),
        Index('idx_unit_status', 'status'),
        Index('idx_unit_active', 'is_active'),
        Index('idx_unit_deleted', 'is_deleted'),
        Index('idx_unit_city', 'city'),
        Index('idx_unit_country', 'country'),
        Index('idx_unit_property_type', 'property_type'),
        Index('idx_unit_brand', 'brand'),
        Index('idx_unit_managers', 'general_manager_id', 'procurement_manager_id'),
        Index('idx_unit_location', 'city', 'state_province', 'country'),
        Index('idx_unit_search', 'name', 'unit_code', 'city', 'brand'),  # Composite search index
    )

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

    @property
    def is_operational(self) -> bool:
        """Check if unit is operational (active and not deleted)."""
        return self.is_active and not self.is_deleted and self.status == "active"

    @property
    def display_title(self) -> str:
        """Get display title for UI."""
        if self.display_name:
            return self.display_name
        return f"{self.name} ({self.unit_code})"

    @property
    def coordinates(self) -> tuple:
        """Get geographic coordinates as tuple."""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None

    def __repr__(self):
        return f"<Unit(id='{self.id}', name='{self.name}', code='{self.unit_code}')>"


class UnitConfig(Base):
    """
    Configuration settings specific to each hotel unit.
    Stores operational parameters, preferences, and customizable settings.
    """
    __tablename__ = "unit_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, unique=True)
    
    # Procurement settings
    auto_approve_limit = Column(Numeric(10, 2), default=100.00)  # Auto-approve orders below this amount
    require_dual_approval = Column(Boolean, default=False)  # Require two approvals
    emergency_procurement_enabled = Column(Boolean, default=True)
    bulk_order_threshold = Column(Numeric(10, 2), default=1000.00)  # Threshold for bulk order discounts
    
    # Inventory management
    low_stock_threshold_days = Column(Integer, default=7)  # Days of inventory to trigger reorder
    auto_reorder_enabled = Column(Boolean, default=False)  # Enable automatic reordering
    inventory_review_frequency = Column(String(20), default="weekly")  # "daily", "weekly", "monthly"
    cycle_count_frequency = Column(String(20), default="monthly")
    
    # Supplier management
    preferred_suppliers_only = Column(Boolean, default=False)  # Only use preferred suppliers
    supplier_diversity_required = Column(Boolean, default=False)  # Require diverse supplier base
    local_supplier_preference = Column(Boolean, default=True)  # Prefer local suppliers
    supplier_performance_review_frequency = Column(String(20), default="quarterly")
    
    # Financial controls
    budget_variance_alert_threshold = Column(Numeric(5, 2), default=10.00)  # Percentage variance alert
    cost_center_tracking_enabled = Column(Boolean, default=True)
    expense_categories_required = Column(Boolean, default=True)
    multi_currency_enabled = Column(Boolean, default=False)
    
    # Operational preferences
    working_hours = Column(JSONB, default={"monday": "9-17", "tuesday": "9-17", "wednesday": "9-17", 
                                          "thursday": "9-17", "friday": "9-17", "saturday": "closed", "sunday": "closed"})
    delivery_window = Column(JSONB, default={"start": "8:00", "end": "16:00"})
    preferred_delivery_days = Column(JSONB, default=["monday", "tuesday", "wednesday", "thursday", "friday"])
    
    # Communication settings
    order_confirmation_required = Column(Boolean, default=True)
    email_notifications_enabled = Column(Boolean, default=True)
    sms_notifications_enabled = Column(Boolean, default=False)
    notification_recipients = Column(JSONB)  # Email addresses for notifications
    
    # Quality and compliance
    quality_inspection_required = Column(Boolean, default=True)
    batch_tracking_enabled = Column(Boolean, default=True)
    expiry_date_tracking = Column(Boolean, default=True)
    food_safety_compliance = Column(Boolean, default=True)
    
    # Reporting and analytics
    daily_reports_enabled = Column(Boolean, default=True)
    weekly_summary_enabled = Column(Boolean, default=True)
    performance_dashboards_enabled = Column(Boolean, default=True)
    cost_analysis_frequency = Column(String(20), default="monthly")
    
    # Integration settings
    pos_integration_enabled = Column(Boolean, default=False)
    erp_integration_enabled = Column(Boolean, default=False)
    accounting_system_sync = Column(Boolean, default=True)
    third_party_integrations = Column(JSONB)  # Third-party system configurations
    
    # Custom settings (flexible)
    custom_fields = Column(JSONB, default=dict)  # Unit-specific custom configurations
    feature_flags = Column(JSONB, default=dict)  # Feature toggles
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit", back_populates="config")
    updater = relationship("User")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("auto_approve_limit >= 0", 
                       name='chk_config_auto_approve_limit_non_negative'),
        CheckConstraint("bulk_order_threshold >= 0", 
                       name='chk_config_bulk_threshold_non_negative'),
        CheckConstraint("low_stock_threshold_days > 0", 
                       name='chk_config_stock_threshold_positive'),
        CheckConstraint("budget_variance_alert_threshold >= 0 AND budget_variance_alert_threshold <= 100", 
                       name='chk_config_variance_threshold_range'),
        CheckConstraint("inventory_review_frequency IN ('daily', 'weekly', 'monthly')", 
                       name='chk_config_review_frequency_valid'),
        CheckConstraint("cycle_count_frequency IN ('weekly', 'monthly', 'quarterly')", 
                       name='chk_config_cycle_count_frequency_valid'),
        CheckConstraint("supplier_performance_review_frequency IN ('monthly', 'quarterly', 'annually')", 
                       name='chk_config_supplier_review_frequency_valid'),
        CheckConstraint("cost_analysis_frequency IN ('weekly', 'monthly', 'quarterly')", 
                       name='chk_config_cost_analysis_frequency_valid'),
        Index('idx_unit_config_unit', 'unit_id'),
        Index('idx_unit_config_auto_approve', 'auto_approve_limit'),
        Index('idx_unit_config_updated', 'updated_at'),
    )

    def __repr__(self):
        return f"<UnitConfig(id='{self.id}', unit_id='{self.unit_id}')>"


class UnitBudget(Base):
    """
    Annual budget management for hotel units.
    Tracks budget allocation, spending, and variance analysis by category.
    """
    __tablename__ = "unit_budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Budget period
    budget_year = Column(Integer, nullable=False, index=True)
    budget_period = Column(String(20), default="annual")  # "annual", "quarterly", "monthly"
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Total budget
    total_budget = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD")
    
    # Category-wise budget allocation
    category_budgets = Column(JSONB, default=dict)  # {"F&B": 50000, "Housekeeping": 30000, ...}
    department_budgets = Column(JSONB, default=dict)  # Department-wise allocation
    
    # Spending tracking (calculated fields updated by triggers/procedures)
    total_spent = Column(Numeric(15, 2), default=0)
    total_committed = Column(Numeric(15, 2), default=0)  # Outstanding orders
    total_available = Column(Numeric(15, 2), default=0)  # Available balance
    
    # Category spending (updated from actual orders)
    category_spending = Column(JSONB, default=dict)
    department_spending = Column(JSONB, default=dict)
    
    # Budget adjustments
    adjustments_total = Column(Numeric(15, 2), default=0)
    adjustment_history = Column(JSONB, default=list)  # History of budget adjustments
    
    # Variance tracking
    variance_amount = Column(Numeric(15, 2), default=0)  # Total variance
    variance_percentage = Column(Numeric(5, 2), default=0)  # Variance as percentage
    variance_analysis = Column(JSONB)  # Detailed variance analysis
    
    # Performance metrics
    utilization_rate = Column(Numeric(5, 2), default=0)  # Budget utilization percentage
    burn_rate = Column(Numeric(10, 2), default=0)  # Monthly burn rate
    projected_year_end = Column(Numeric(15, 2))  # Projected year-end spending
    
    # Approval and controls
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approval_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="draft")  # "draft", "approved", "active", "closed"
    
    # Alerts and notifications
    alert_thresholds = Column(JSONB, default={"warning": 80, "critical": 95})  # Percentage thresholds
    last_alert_sent = Column(DateTime(timezone=True))
    alert_recipients = Column(JSONB)  # Email addresses for budget alerts
    
    # Review and planning
    quarterly_reviews = Column(JSONB, default=list)  # Quarterly review notes
    next_review_date = Column(DateTime(timezone=True))
    planning_notes = Column(Text)
    
    # Comparative analysis
    previous_year_budget = Column(Numeric(15, 2))
    previous_year_actual = Column(Numeric(15, 2))
    growth_rate = Column(Numeric(5, 2))  # Budget growth compared to previous year
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Version control
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)  # Current active budget version
    
    # Relationships
    unit = relationship("Unit", back_populates="budgets")
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one current budget per unit per year
        Index('idx_unit_budget_current_unique', 'unit_id', 'budget_year', 'is_current', unique=True,
              postgresql_where=Column('is_current') == True),
        CheckConstraint("period_start < period_end", 
                       name='chk_budget_period_valid'),
        CheckConstraint("total_budget >= 0", 
                       name='chk_budget_total_non_negative'),
        CheckConstraint("total_spent >= 0", 
                       name='chk_budget_spent_non_negative'),
        CheckConstraint("total_committed >= 0", 
                       name='chk_budget_committed_non_negative'),
        CheckConstraint("budget_period IN ('annual', 'quarterly', 'monthly')", 
                       name='chk_budget_period_type_valid'),
        CheckConstraint("status IN ('draft', 'approved', 'active', 'closed', 'revised')", 
                       name='chk_budget_status_valid'),
        CheckConstraint("utilization_rate >= 0 AND utilization_rate <= 200", 
                       name='chk_budget_utilization_range'),
        CheckConstraint("variance_percentage >= -100", 
                       name='chk_budget_variance_range'),
        CheckConstraint("version > 0", 
                       name='chk_budget_version_positive'),
        Index('idx_unit_budget_unit', 'unit_id'),
        Index('idx_unit_budget_year', 'budget_year'),
        Index('idx_unit_budget_period', 'period_start', 'period_end'),
        Index('idx_unit_budget_status', 'status'),
        Index('idx_unit_budget_current', 'is_current'),
        Index('idx_unit_budget_utilization', 'utilization_rate'),
        Index('idx_unit_budget_variance', 'variance_percentage'),
        Index('idx_unit_budget_review', 'next_review_date'),
    )

    @property
    def remaining_budget(self) -> Decimal:
        """Calculate remaining budget amount."""
        return self.total_budget - self.total_spent - self.total_committed

    @property
    def is_over_budget(self) -> bool:
        """Check if spending exceeds budget."""
        return (self.total_spent + self.total_committed) > self.total_budget

    @property
    def days_remaining(self) -> int:
        """Get number of days remaining in budget period."""
        if self.period_end:
            delta = self.period_end - datetime.utcnow()
            return max(0, delta.days)
        return 0

    @property
    def budget_health_status(self) -> str:
        """Get budget health status based on utilization and variance."""
        if self.utilization_rate >= 95:
            return "critical"
        elif self.utilization_rate >= 80:
            return "warning"
        elif self.utilization_rate >= 60:
            return "on_track"
        else:
            return "under_utilized"

    @property
    def projected_overrun(self) -> Decimal:
        """Calculate projected budget overrun based on current burn rate."""
        if self.burn_rate > 0 and self.days_remaining > 0:
            projected_total = self.total_spent + (self.burn_rate * (self.days_remaining / 30))
            return max(0, projected_total - self.total_budget)
        return Decimal('0.00')

    def __repr__(self):
        return f"<UnitBudget(id='{self.id}', unit_id='{self.unit_id}', year={self.budget_year}, total={self.total_budget})>"


class UnitPerformanceMetric(Base):
    """
    Track key performance indicators (KPIs) for hotel units.
    Stores time-series data for procurement performance analysis.
    """
    __tablename__ = "unit_performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Metric period
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly", "quarterly"
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Procurement metrics
    total_orders = Column(Integer, default=0)
    total_order_value = Column(Numeric(15, 2), default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    order_fulfillment_rate = Column(Numeric(5, 2), default=0)  # Percentage
    
    # Supplier performance
    active_suppliers = Column(Integer, default=0)
    supplier_performance_score = Column(Numeric(5, 2), default=0)  # Average supplier rating
    on_time_delivery_rate = Column(Numeric(5, 2), default=0)
    quality_score = Column(Numeric(5, 2), default=0)
    
    # Inventory metrics
    inventory_turnover = Column(Numeric(8, 2), default=0)
    stock_out_incidents = Column(Integer, default=0)
    excess_inventory_value = Column(Numeric(12, 2), default=0)
    inventory_accuracy = Column(Numeric(5, 2), default=0)
    
    # Financial metrics
    cost_savings_achieved = Column(Numeric(12, 2), default=0)
    budget_variance = Column(Numeric(5, 2), default=0)  # Percentage variance
    cost_per_room = Column(Numeric(8, 2), default=0)  # Cost per occupied room
    procurement_roi = Column(Numeric(5, 2), default=0)  # Return on investment
    
    # Efficiency metrics
    approval_cycle_time = Column(Numeric(6, 2), default=0)  # Average approval time in hours
    procurement_cycle_time = Column(Numeric(6, 2), default=0)  # Order to delivery time
    automation_rate = Column(Numeric(5, 2), default=0)  # Percentage of automated orders
    error_rate = Column(Numeric(5, 2), default=0)  # Order error percentage
    
    # Sustainability metrics
    local_supplier_percentage = Column(Numeric(5, 2), default=0)
    sustainable_products_percentage = Column(Numeric(5, 2), default=0)
    waste_reduction_percentage = Column(Numeric(5, 2), default=0)
    carbon_footprint_score = Column(Numeric(8, 2), default=0)
    
    # Compliance metrics
    compliance_score = Column(Numeric(5, 2), default=0)
    audit_findings = Column(Integer, default=0)
    policy_violations = Column(Integer, default=0)
    training_completion_rate = Column(Numeric(5, 2), default=0)
    
    # Operational metrics
    staff_productivity_score = Column(Numeric(5, 2), default=0)
    system_uptime_percentage = Column(Numeric(5, 2), default=0)
    user_satisfaction_score = Column(Numeric(5, 2), default=0)
    process_improvement_count = Column(Integer, default=0)
    
    # Benchmarking data
    industry_benchmark_score = Column(Numeric(5, 2))  # Compared to industry average
    peer_comparison_score = Column(Numeric(5, 2))  # Compared to similar units
    year_over_year_growth = Column(Numeric(5, 2))  # Growth compared to previous period
    
    # Additional metrics (flexible)
    custom_metrics = Column(JSONB, default=dict)  # Unit-specific custom metrics
    notes = Column(Text)
    
    # Data quality
    data_completeness = Column(Numeric(5, 2), default=100)  # Percentage of complete data
    calculation_method = Column(String(100))  # How metrics were calculated
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    creator = relationship("User")

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one metric record per unit per period
        Index('idx_unit_metric_unique', 'unit_id', 'period_start', 'period_end', 'period_type', unique=True),
        CheckConstraint("period_start < period_end", 
                       name='chk_metric_period_valid'),
        CheckConstraint("period_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')", 
                       name='chk_metric_period_type_valid'),
        CheckConstraint("total_orders >= 0", 
                       name='chk_metric_orders_non_negative'),
        CheckConstraint("order_fulfillment_rate >= 0 AND order_fulfillment_rate <= 100", 
                       name='chk_metric_fulfillment_rate_range'),
        CheckConstraint("supplier_performance_score >= 0 AND supplier_performance_score <= 100", 
                       name='chk_metric_supplier_score_range'),
        CheckConstraint("inventory_accuracy >= 0 AND inventory_accuracy <= 100", 
                       name='chk_metric_inventory_accuracy_range'),
        CheckConstraint("data_completeness >= 0 AND data_completeness <= 100", 
                       name='chk_metric_data_completeness_range'),
        Index('idx_unit_metric_unit', 'unit_id'),
        Index('idx_unit_metric_date', 'metric_date'),
        Index('idx_unit_metric_period', 'period_type'),
        Index('idx_unit_metric_performance', 'supplier_performance_score'),
        Index('idx_unit_metric_budget_variance', 'budget_variance'),
        Index('idx_unit_metric_efficiency', 'procurement_cycle_time'),
        Index('idx_unit_metric_created', 'created_at'),
    )

    @property
    def overall_performance_score(self) -> float:
        """Calculate overall performance score as weighted average."""
        weights = {
            'supplier_performance_score': 0.25,
            'order_fulfillment_rate': 0.20,
            'inventory_accuracy': 0.15,
            'compliance_score': 0.15,
            'cost_savings_achieved': 0.10,
            'staff_productivity_score': 0.10,
            'user_satisfaction_score': 0.05
        }
        
        total_score = 0
        total_weight = 0
        
        for metric, weight in weights.items():
            value = getattr(self, metric, 0)
            if value and value > 0:
                total_score += float(value) * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0

    def __repr__(self):
        return f"<UnitPerformanceMetric(unit_id='{self.unit_id}', period='{self.period_start}' to '{self.period_end}')>"