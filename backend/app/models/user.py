from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base


class User(Base):
    """
    Main user model for authentication and authorization.
    Supports multi-tenant access through unit assignments and role-based permissions.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic user information
    email = Column(String(200), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)  # Optional username
    hashed_password = Column(String(200), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))  # Job title
    department = Column(String(100))
    
    # Contact information
    phone = Column(String(50))
    mobile = Column(String(50))
    extension = Column(String(10))
    
    # Role and permissions
    role = Column(String(50), nullable=False, index=True)  # "superuser", "procurement_admin", "unit_manager", "store_manager", "store_staff", "supplier_user"
    is_superuser = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Profile and preferences
    profile_picture_url = Column(String(500))
    language = Column(String(10), default="en")  # ISO language code
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")
    time_format = Column(String(10), default="24h")  # "12h" or "24h"
    
    # User preferences (JSON stored settings)
    preferences = Column(JSONB, default=dict)  # User-specific settings and preferences
    notification_settings = Column(JSONB, default=dict)  # Email, SMS, push notification preferences
    dashboard_settings = Column(JSONB, default=dict)  # Dashboard layout and widget preferences
    
    # Authentication and session management
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))  # Account lockout timestamp
    
    # Password management
    password_changed_at = Column(DateTime(timezone=True))
    password_expires_at = Column(DateTime(timezone=True))
    must_change_password = Column(Boolean, default=False)  # Force password change on next login
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(200))  # TOTP secret
    backup_codes = Column(JSONB)  # List of backup codes
    
    # Terms and compliance
    terms_accepted_at = Column(DateTime(timezone=True))
    privacy_policy_accepted_at = Column(DateTime(timezone=True))
    data_retention_consent = Column(Boolean, default=True)
    
    # Employment information
    employee_id = Column(String(50), unique=True, index=True)
    hire_date = Column(DateTime(timezone=True))
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Direct manager
    cost_center = Column(String(50))  # For budgeting and reporting
    
    # Status and lifecycle
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="active", nullable=False)  # "active", "inactive", "suspended", "terminated"
    termination_date = Column(DateTime(timezone=True))
    termination_reason = Column(String(200))
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    notes = Column(Text)  # Internal notes about the user
    emergency_contact = Column(JSONB)  # Emergency contact information
    skills_certifications = Column(JSONB)  # Professional skills and certifications
    
    # Relationships
    unit_assignments = relationship("UserUnitAssignment", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    managed_users = relationship("User", foreign_keys="User.manager_id", remote_side=[id])
    
    # Audit relationships (explicit foreign_keys to avoid confusion)
    creator = relationship("User", foreign_keys=[created_by], remote_side=[id], post_update=True)
    updater = relationship("User", foreign_keys=[updated_by], remote_side=[id], post_update=True)
    deleter = relationship("User", foreign_keys=[deleted_by], remote_side=[id], post_update=True)

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("role IN ('superuser', 'procurement_admin', 'unit_manager', 'store_manager', 'store_staff', 'supplier_user')", 
                       name='chk_user_role_valid'),
        CheckConstraint("status IN ('active', 'inactive', 'suspended', 'terminated')", 
                       name='chk_user_status_valid'),
        CheckConstraint("time_format IN ('12h', '24h')", 
                       name='chk_user_time_format_valid'),
        CheckConstraint("failed_login_attempts >= 0", 
                       name='chk_user_failed_attempts_non_negative'),
        CheckConstraint("login_count >= 0", 
                       name='chk_user_login_count_non_negative'),
        CheckConstraint("email_verified = false OR email_verified_at IS NOT NULL", 
                       name='chk_user_email_verification_consistency'),
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_employee_id', 'employee_id'),
        Index('idx_user_role', 'role'),
        Index('idx_user_status', 'status'),
        Index('idx_user_active', 'is_active'),
        Index('idx_user_superuser', 'is_superuser'),
        Index('idx_user_deleted', 'is_deleted'),
        Index('idx_user_name', 'first_name', 'last_name'),
        Index('idx_user_department', 'department'),
        Index('idx_user_manager', 'manager_id'),
        Index('idx_user_last_login', 'last_login_at'),
        Index('idx_user_locked', 'locked_until'),
        Index('idx_user_search', 'first_name', 'last_name', 'email', 'employee_id'),  # Composite search index
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_account_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False

    @property
    def is_password_expired(self) -> bool:
        """Check if password has expired."""
        if self.password_expires_at:
            return datetime.utcnow() > self.password_expires_at
        return False

    @property
    def is_authenticated_user(self) -> bool:
        """Check if user can authenticate (active, not locked, not deleted)."""
        return (self.is_active and 
                not self.is_deleted and 
                not self.is_account_locked and 
                self.status == "active")

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.title:
            return f"{self.full_name} ({self.title})"
        return self.full_name

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return self.role == role

    def has_any_role(self, roles: list) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"


class UserUnitAssignment(Base):
    """
    Many-to-many relationship between users and hotel units.
    Enables multi-tenant access control where users can be assigned to specific units.
    """
    __tablename__ = "user_unit_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Assignment details
    role = Column(String(50), nullable=False)  # Role specific to this unit: "unit_manager", "store_manager", "store_staff"
    is_primary_unit = Column(Boolean, default=False)  # User's primary/home unit
    
    # Access permissions
    can_approve_orders = Column(Boolean, default=False)
    can_manage_inventory = Column(Boolean, default=True)
    can_manage_suppliers = Column(Boolean, default=False)
    can_view_reports = Column(Boolean, default=True)
    approval_limit = Column(Integer, default=0)  # Dollar amount user can approve
    
    # Assignment lifecycle
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    effective_date = Column(DateTime(timezone=True), server_default=func.now())
    expiry_date = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    removed_at = Column(DateTime(timezone=True))
    removed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    removal_reason = Column(String(200))
    
    # Work schedule and availability (optional)
    work_schedule = Column(JSONB)  # {"monday": "9-17", "tuesday": "9-17", ...}
    shift_type = Column(String(50))  # "day", "night", "rotating"
    
    # Performance and metrics (unit-specific)
    performance_rating = Column(Integer)  # 1-5 rating for this unit
    last_performance_review = Column(DateTime(timezone=True))
    objectives = Column(JSONB)  # Unit-specific objectives and KPIs
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Additional information
    notes = Column(Text)
    special_access = Column(JSONB)  # Special permissions or restrictions
    
    # Relationships
    user = relationship("User", back_populates="unit_assignments", foreign_keys=[user_id])
    unit = relationship("Unit")
    assigner = relationship("User", foreign_keys=[assigned_by])
    remover = relationship("User", foreign_keys=[removed_by])

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one active assignment per user per unit
        Index('idx_user_unit_active_unique', 'user_id', 'unit_id', 'is_active', unique=True, 
              postgresql_where=Column('is_active') == True),
        CheckConstraint("role IN ('unit_manager', 'store_manager', 'store_staff', 'supplier_liaison')", 
                       name='chk_assignment_role_valid'),
        CheckConstraint("approval_limit >= 0", 
                       name='chk_assignment_approval_limit_non_negative'),
        CheckConstraint("performance_rating IS NULL OR (performance_rating >= 1 AND performance_rating <= 5)", 
                       name='chk_assignment_performance_rating_range'),
        CheckConstraint("effective_date <= expiry_date OR expiry_date IS NULL", 
                       name='chk_assignment_dates_valid'),
        Index('idx_user_unit_user', 'user_id'),
        Index('idx_user_unit_unit', 'unit_id'),
        Index('idx_user_unit_role', 'role'),
        Index('idx_user_unit_active', 'is_active'),
        Index('idx_user_unit_primary', 'is_primary_unit'),
        Index('idx_user_unit_assigned', 'assigned_at'),
        Index('idx_user_unit_expiry', 'expiry_date'),
        Index('idx_user_unit_permissions', 'can_approve_orders', 'approval_limit'),
    )

    @property
    def is_current_assignment(self) -> bool:
        """Check if assignment is currently valid."""
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.effective_date and now < self.effective_date:
            return False
        if self.expiry_date and now > self.expiry_date:
            return False
        return True

    @property
    def assignment_duration_days(self) -> int:
        """Get duration of assignment in days."""
        end_date = self.removed_at or self.expiry_date or datetime.utcnow()
        start_date = self.effective_date or self.assigned_at
        return (end_date - start_date).days

    def __repr__(self):
        return f"<UserUnitAssignment(user_id='{self.user_id}', unit_id='{self.unit_id}', role='{self.role}')>"


class UserActivity(Base):
    """
    Audit log for user activities and system events.
    Tracks all significant user actions for security, compliance, and analytics.
    """
    __tablename__ = "user_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)  # "login", "logout", "order_created", "password_changed", etc.
    description = Column(String(500), nullable=False)
    category = Column(String(50))  # "authentication", "order_management", "user_management", "system"
    
    # Context information
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"))  # Unit context if applicable
    resource_type = Column(String(100))  # "product", "order", "user", "supplier"
    resource_id = Column(UUID(as_uuid=True))  # ID of the affected resource
    
    # Technical details
    ip_address = Column(String(45))  # IPv4 or IPv6 address
    user_agent = Column(String(500))  # Browser/client information
    session_id = Column(String(200))  # Session identifier
    request_id = Column(String(200))  # Request tracking ID
    
    # Request details
    http_method = Column(String(10))  # GET, POST, PUT, DELETE
    endpoint = Column(String(200))  # API endpoint accessed
    response_code = Column(Integer)  # HTTP response code
    response_time_ms = Column(Integer)  # Response time in milliseconds
    
    # Location information
    geolocation = Column(JSONB)  # {"country": "US", "city": "New York", "lat": 40.7128, "lng": -74.0060}
    timezone_offset = Column(Integer)  # UTC offset in minutes
    
    # Additional metadata
    user_metadata = Column(JSONB, default=dict)  # Flexible additional data
    old_values = Column(JSONB)  # Previous values for update operations
    new_values = Column(JSONB)  # New values for update operations
    
    # Risk and security
    risk_score = Column(Integer, default=0)  # Calculated risk score for this activity
    is_suspicious = Column(Boolean, default=False)  # Flagged as potentially suspicious
    security_flags = Column(JSONB)  # Security-related flags and alerts
    
    # Audit and compliance
    severity = Column(String(20), default="info")  # "info", "warning", "error", "critical"
    compliance_relevant = Column(Boolean, default=False)  # Relevant for compliance reporting
    retention_period_days = Column(Integer, default=2555)  # 7 years default retention
    
    # Relationships and references
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Who performed the action (for admin actions)
    parent_activity_id = Column(UUID(as_uuid=True), ForeignKey("user_activities.id"))  # Related parent activity
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True))  # When this record should be purged
    
    # Relationships
    user = relationship("User", back_populates="activities", foreign_keys=[user_id])
    unit = relationship("Unit")
    performer = relationship("User", foreign_keys=[performed_by])
    parent_activity = relationship("UserActivity", remote_side=[id], foreign_keys=[parent_activity_id])
    child_activities = relationship("UserActivity", foreign_keys="UserActivity.parent_activity_id")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("severity IN ('info', 'warning', 'error', 'critical')", 
                       name='chk_activity_severity_valid'),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", 
                       name='chk_activity_risk_score_range'),
        CheckConstraint("response_time_ms IS NULL OR response_time_ms >= 0", 
                       name='chk_activity_response_time_non_negative'),
        CheckConstraint("retention_period_days > 0", 
                       name='chk_activity_retention_positive'),
        Index('idx_user_activity_user', 'user_id'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_category', 'category'),
        Index('idx_user_activity_created', 'created_at'),
        Index('idx_user_activity_unit', 'unit_id'),
        Index('idx_user_activity_resource', 'resource_type', 'resource_id'),
        Index('idx_user_activity_ip', 'ip_address'),
        Index('idx_user_activity_session', 'session_id'),
        Index('idx_user_activity_suspicious', 'is_suspicious'),
        Index('idx_user_activity_severity', 'severity'),
        Index('idx_user_activity_compliance', 'compliance_relevant'),
        Index('idx_user_activity_expires', 'expires_at'),
        Index('idx_user_activity_security', 'user_id', 'created_at', 'is_suspicious'),  # Security analysis
        Index('idx_user_activity_audit', 'user_id', 'activity_type', 'created_at'),  # Audit queries
    )

    @property
    def is_high_risk(self) -> bool:
        """Check if activity is considered high risk."""
        return self.risk_score >= 70 or self.is_suspicious

    @property
    def is_expired(self) -> bool:
        """Check if activity record has expired and should be purged."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def age_days(self) -> int:
        """Get age of activity record in days."""
        return (datetime.utcnow() - self.created_at).days

    def __repr__(self):
        return f"<UserActivity(id='{self.id}', user_id='{self.user_id}', type='{self.activity_type}')>"


class UserSession(Base):
    """
    Track active user sessions for security and session management.
    Helps with concurrent session limits and security monitoring.
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session identification
    session_token = Column(String(200), unique=True, nullable=False, index=True)
    refresh_token = Column(String(200), unique=True, index=True)
    session_type = Column(String(50), default="web")  # "web", "mobile", "api"
    
    # Session details
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500))
    device_fingerprint = Column(String(200))  # Device identification
    
    # Location and context
    geolocation = Column(JSONB)
    timezone = Column(String(50))
    unit_context = Column(UUID(as_uuid=True), ForeignKey("units.id"))  # Current unit context
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    logout_at = Column(DateTime(timezone=True))
    logout_reason = Column(String(100))  # "user_logout", "timeout", "admin_revoke", "security"
    
    # Security flags
    is_trusted_device = Column(Boolean, default=False)
    requires_2fa = Column(Boolean, default=False)
    security_warnings = Column(JSONB)  # Security-related warnings or flags
    
    # Relationships
    user = relationship("User")
    current_unit = relationship("Unit")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("session_type IN ('web', 'mobile', 'api', 'desktop')", 
                       name='chk_session_type_valid'),
        CheckConstraint("logout_reason IS NULL OR logout_reason IN ('user_logout', 'timeout', 'admin_revoke', 'security', 'expired')", 
                       name='chk_session_logout_reason_valid'),
        Index('idx_user_session_user', 'user_id'),
        Index('idx_user_session_token', 'session_token'),
        Index('idx_user_session_refresh', 'refresh_token'),
        Index('idx_user_session_active', 'is_active'),
        Index('idx_user_session_expires', 'expires_at'),
        Index('idx_user_session_last_activity', 'last_activity_at'),
        Index('idx_user_session_ip', 'ip_address'),
        Index('idx_user_session_cleanup', 'is_active', 'expires_at'),  # For cleanup queries
    )

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid and active."""
        return self.is_active and not self.is_expired

    @property
    def session_duration_minutes(self) -> int:
        """Get session duration in minutes."""
        end_time = self.logout_at or datetime.utcnow()
        return int((end_time - self.created_at).total_seconds() / 60)

    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', active={self.is_active})>"