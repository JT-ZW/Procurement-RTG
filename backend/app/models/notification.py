"""
Notification and Communication Models
Handles system notifications, alerts, and communication tracking.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Enum, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    REMINDER = "reminder"
    APPROVAL_REQUEST = "approval_request"
    DEADLINE_ALERT = "deadline_alert"
    BUDGET_ALERT = "budget_alert"
    SYSTEM_ALERT = "system_alert"


class NotificationStatus(str, enum.Enum):
    """Notification status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommunicationChannel(str, enum.Enum):
    """Communication channels."""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"
    SLACK = "slack"
    TEAMS = "teams"


class Notification(Base):
    """
    Main notification model.
    Handles all types of system notifications and alerts.
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    notification_number = Column(String(100), unique=True, nullable=False, index=True)
    
    # Multi-tenant
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), index=True)
    
    # Notification details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    priority = Column(String(20), default="medium", index=True)  # "low", "medium", "high", "urgent"
    
    # Recipient information
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    recipient_role = Column(String(50))  # For role-based notifications
    recipient_email = Column(String(200))
    recipient_phone = Column(String(50))
    
    # Source information
    source_type = Column(String(50))  # "requisition", "purchase_order", "invoice", "budget", "system"
    source_id = Column(UUID(as_uuid=True))
    source_reference = Column(String(100))  # Human-readable reference
    
    # Delivery settings
    delivery_channels = Column(JSONB, default=["in_app"])  # Channels to use for delivery
    immediate_delivery = Column(Boolean, default=False)
    scheduled_delivery_time = Column(DateTime(timezone=True))
    
    # Status tracking
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    
    # Delivery tracking
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Failure handling
    failure_reason = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True))
    
    # Action information
    action_required = Column(Boolean, default=False)
    action_url = Column(String(500))  # Deep link to relevant page
    action_button_text = Column(String(100))
    action_deadline = Column(DateTime(timezone=True))
    
    # Grouping and categorization
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    tags = Column(JSONB)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    auto_delete_after_read = Column(Boolean, default=False)
    
    # Template information
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"))
    template_variables = Column(JSONB)  # Variables used to populate template
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    recipient = relationship("User", foreign_keys=[recipient_user_id])
    template = relationship("NotificationTemplate")
    creator = relationship("User", foreign_keys=[created_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="notification", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("retry_count >= 0", name='chk_notification_retry_count_non_negative'),
        CheckConstraint("max_retries >= 0", name='chk_notification_max_retries_non_negative'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='chk_notification_priority_valid'),
        Index('idx_notification_recipient_status', 'recipient_user_id', 'status'),
        Index('idx_notification_type_priority', 'notification_type', 'priority'),
        Index('idx_notification_source', 'source_type', 'source_id'),
        Index('idx_notification_scheduled', 'scheduled_delivery_time'),
        Index('idx_notification_expiry', 'expires_at'),
        Index('idx_notification_category', 'category', 'subcategory'),
    )


class NotificationTemplate(Base):
    """
    Notification templates for consistent messaging.
    Defines reusable notification formats.
    """
    __tablename__ = "notification_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    template_code = Column(String(100), unique=True, nullable=False, index=True)
    template_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Multi-tenant
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), index=True)
    is_global = Column(Boolean, default=False)  # Available to all units
    
    # Template content
    title_template = Column(String(500), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Channel-specific templates
    email_subject_template = Column(String(500))
    email_body_template = Column(Text)
    sms_template = Column(String(500))
    push_title_template = Column(String(200))
    push_body_template = Column(String(500))
    
    # Template settings
    notification_type = Column(Enum(NotificationType), nullable=False)
    default_priority = Column(String(20), default="medium")
    default_channels = Column(JSONB, default=["in_app"])
    
    # Variables
    required_variables = Column(JSONB)  # List of required template variables
    optional_variables = Column(JSONB)  # List of optional template variables
    variable_descriptions = Column(JSONB)  # Help text for variables
    
    # Behavior settings
    action_required = Column(Boolean, default=False)
    action_button_text = Column(String(100))
    action_url_template = Column(String(500))
    expires_after_hours = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Version tracking
    version = Column(Integer, default=1)
    is_latest_version = Column(Boolean, default=True)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"))
    
    # Relationships
    unit = relationship("Unit")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    previous_version = relationship("NotificationTemplate", remote_side=[id])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("expires_after_hours IS NULL OR expires_after_hours > 0", 
                       name='chk_template_expiry_hours_positive'),
        CheckConstraint("version > 0", name='chk_template_version_positive'),
        CheckConstraint("default_priority IN ('low', 'medium', 'high', 'urgent')", 
                       name='chk_template_priority_valid'),
        Index('idx_template_unit_type', 'unit_id', 'notification_type'),
        Index('idx_template_active', 'is_active'),
        Index('idx_template_global', 'is_global'),
    )


class NotificationDeliveryLog(Base):
    """
    Delivery log for notifications.
    Tracks delivery attempts and outcomes for each channel.
    """
    __tablename__ = "notification_delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent notification
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=False, index=True)
    
    # Delivery details
    delivery_channel = Column(Enum(CommunicationChannel), nullable=False)
    delivery_address = Column(String(200))  # Email address, phone number, etc.
    
    # Attempt information
    attempt_number = Column(Integer, default=1)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Status
    delivery_status = Column(String(50), nullable=False)  # "pending", "sent", "delivered", "failed", "bounced"
    
    # Success information
    delivered_at = Column(DateTime(timezone=True))
    external_id = Column(String(200))  # ID from external service (e.g., email service)
    external_reference = Column(String(200))
    
    # Failure information
    failure_reason = Column(Text)
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Provider information
    service_provider = Column(String(100))  # "SendGrid", "Twilio", etc.
    provider_response = Column(JSONB)  # Full response from provider
    
    # Cost tracking
    delivery_cost = Column(Numeric(10, 4))  # Cost of delivery (e.g., SMS cost)
    currency = Column(String(3))
    
    # Relationships
    notification = relationship("Notification", back_populates="delivery_logs")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("attempt_number > 0", name='chk_delivery_log_attempt_positive'),
        CheckConstraint("delivery_cost IS NULL OR delivery_cost >= 0", name='chk_delivery_log_cost_non_negative'),
        Index('idx_delivery_log_notification', 'notification_id'),
        Index('idx_delivery_log_channel', 'delivery_channel'),
        Index('idx_delivery_log_status', 'delivery_status'),
        Index('idx_delivery_log_attempted', 'attempted_at'),
    )


class NotificationPreference(Base):
    """
    User notification preferences.
    Controls how users want to receive different types of notifications.
    """
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Unit-specific preferences (optional)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), index=True)
    
    # Notification type and category
    notification_type = Column(Enum(NotificationType), index=True)
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    
    # Timing preferences
    immediate_delivery = Column(Boolean, default=False)
    digest_mode = Column(Boolean, default=False)  # Batch notifications
    digest_frequency = Column(String(20), default="daily")  # "hourly", "daily", "weekly"
    digest_time = Column(String(10), default="09:00")  # Time for digest delivery
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(10))  # "22:00"
    quiet_hours_end = Column(String(10))    # "08:00"
    quiet_hours_timezone = Column(String(50))
    
    # Weekend and holiday preferences
    weekend_delivery = Column(Boolean, default=True)
    holiday_delivery = Column(Boolean, default=False)
    
    # Priority filtering
    minimum_priority = Column(String(20), default="low")  # Only receive notifications of this priority or higher
    
    # Escalation preferences
    escalation_enabled = Column(Boolean, default=True)
    escalation_channels = Column(JSONB)  # Channels to use for escalations
    escalation_delay_minutes = Column(Integer, default=60)
    
    # Contact information
    email_address = Column(String(200))  # Override default email
    phone_number = Column(String(50))    # Override default phone
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    unit = relationship("Unit")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique preference per user/unit/type/category combination
        Index('idx_notification_pref_unique', 'user_id', 'unit_id', 'notification_type', 'category', unique=True),
        CheckConstraint("digest_frequency IN ('hourly', 'daily', 'weekly')", 
                       name='chk_notification_pref_digest_frequency'),
        CheckConstraint("minimum_priority IN ('low', 'medium', 'high', 'urgent')", 
                       name='chk_notification_pref_min_priority'),
        CheckConstraint("escalation_delay_minutes > 0", name='chk_notification_pref_escalation_delay'),
        Index('idx_notification_pref_user', 'user_id'),
        Index('idx_notification_pref_type', 'notification_type'),
    )


class NotificationRule(Base):
    """
    Notification rules for automatic notification generation.
    Defines when and how notifications should be created.
    """
    __tablename__ = "notification_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_name = Column(String(200), nullable=False)
    rule_code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Multi-tenant
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), index=True)
    is_global = Column(Boolean, default=False)
    
    # Trigger conditions
    trigger_event = Column(String(100), nullable=False, index=True)  # "requisition_submitted", "budget_threshold_reached", etc.
    trigger_conditions = Column(JSONB)  # Additional conditions for triggering
    
    # Target specification
    target_type = Column(String(50), nullable=False)  # "user", "role", "department", "unit_managers"
    target_users = Column(JSONB)  # Specific user IDs
    target_roles = Column(JSONB)  # Roles to notify
    target_departments = Column(JSONB)  # Departments to notify
    
    # Notification settings
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=False)
    priority = Column(String(20), default="medium")
    delivery_channels = Column(JSONB, default=["in_app"])
    
    # Timing
    immediate_send = Column(Boolean, default=True)
    delay_minutes = Column(Integer, default=0)
    
    # Frequency control
    max_frequency = Column(String(50))  # "once", "daily", "weekly", "unlimited"
    suppress_duplicates = Column(Boolean, default=True)
    duplicate_check_window_hours = Column(Integer, default=24)
    
    # Escalation
    escalation_enabled = Column(Boolean, default=False)
    escalation_after_hours = Column(Integer, default=24)
    escalation_to_users = Column(JSONB)
    escalation_to_roles = Column(JSONB)
    
    # Status and control
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    execution_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    template = relationship("NotificationTemplate")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("delay_minutes >= 0", name='chk_rule_delay_non_negative'),
        CheckConstraint("escalation_after_hours > 0", name='chk_rule_escalation_hours_positive'),
        CheckConstraint("duplicate_check_window_hours > 0", name='chk_rule_duplicate_window_positive'),
        CheckConstraint("execution_count >= 0", name='chk_rule_execution_count_non_negative'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='chk_rule_priority_valid'),
        CheckConstraint("target_type IN ('user', 'role', 'department', 'unit_managers')", 
                       name='chk_rule_target_type_valid'),
        CheckConstraint("max_frequency IN ('once', 'daily', 'weekly', 'unlimited')", 
                       name='chk_rule_frequency_valid'),
        Index('idx_rule_unit_event', 'unit_id', 'trigger_event'),
        Index('idx_rule_active', 'is_active'),
        Index('idx_rule_last_triggered', 'last_triggered_at'),
    )
