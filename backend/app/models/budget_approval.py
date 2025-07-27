"""
Budget and Approval Workflow Models
Handles budget management and approval processes for procurement.
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


class BudgetType(str, enum.Enum):
    """Types of budgets."""
    OPERATIONAL = "operational"
    CAPITAL = "capital"
    MAINTENANCE = "maintenance"
    PROJECT = "project"
    EMERGENCY = "emergency"


class BudgetStatus(str, enum.Enum):
    """Budget status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CLOSED = "closed"


class ApprovalStatus(str, enum.Enum):
    """Approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class Budget(Base):
    """
    Budget management model.
    Defines spending limits and controls for different categories.
    """
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    budget_code = Column(String(50), unique=True, nullable=False, index=True)
    budget_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Multi-tenant & organization
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, index=True)
    department = Column(String(100), index=True)
    cost_center = Column(String(50), index=True)
    
    # Budget classification
    budget_type = Column(Enum(BudgetType), nullable=False, index=True)
    category = Column(String(100), index=True)  # "F&B", "Housekeeping", "Maintenance", etc.
    subcategory = Column(String(100))
    
    # Financial details
    total_amount = Column(Numeric(15, 2), nullable=False)
    allocated_amount = Column(Numeric(15, 2), default=0)
    committed_amount = Column(Numeric(15, 2), default=0)
    spent_amount = Column(Numeric(15, 2), default=0)
    available_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Period
    fiscal_year = Column(Integer, nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Status and control
    status = Column(Enum(BudgetStatus), default=BudgetStatus.DRAFT, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Approval and authorization
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Budget owner and management
    budget_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    budget_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Controls and limits
    warning_threshold_percentage = Column(Numeric(5, 2), default=80.00)  # Warn at 80%
    freeze_threshold_percentage = Column(Numeric(5, 2), default=95.00)   # Freeze at 95%
    allow_overspend = Column(Boolean, default=False)
    overspend_limit_percentage = Column(Numeric(5, 2), default=5.00)
    
    # Workflow settings
    requires_approval = Column(Boolean, default=True)
    approval_threshold = Column(Numeric(15, 2))  # Amount above which approval is required
    auto_approval_limit = Column(Numeric(15, 2))  # Amount below which auto-approval is allowed
    
    # Notification settings
    notification_recipients = Column(JSONB)  # List of user IDs to notify
    email_notifications_enabled = Column(Boolean, default=True)
    
    # Review and monitoring
    last_reviewed_at = Column(DateTime(timezone=True))
    last_reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    next_review_date = Column(DateTime(timezone=True))
    review_frequency_days = Column(Integer, default=30)
    
    # Rollover and carryover
    allows_rollover = Column(Boolean, default=False)
    rollover_percentage = Column(Numeric(5, 2), default=0.00)
    previous_budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"))
    rollover_amount = Column(Numeric(15, 2), default=0)
    
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
    budget_owner = relationship("User", foreign_keys=[budget_owner_id])
    budget_manager = relationship("User", foreign_keys=[budget_manager_id])
    approver = relationship("User", foreign_keys=[approved_by])
    reviewer = relationship("User", foreign_keys=[last_reviewed_by])
    previous_budget = relationship("Budget", remote_side=[id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    allocations = relationship("BudgetAllocation", back_populates="budget", cascade="all, delete-orphan")
    transactions = relationship("BudgetTransaction", back_populates="budget", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("total_amount > 0", name='chk_budget_total_positive'),
        CheckConstraint("allocated_amount >= 0", name='chk_budget_allocated_non_negative'),
        CheckConstraint("committed_amount >= 0", name='chk_budget_committed_non_negative'),
        CheckConstraint("spent_amount >= 0", name='chk_budget_spent_non_negative'),
        CheckConstraint("available_amount >= 0", name='chk_budget_available_non_negative'),
        CheckConstraint("start_date < end_date", name='chk_budget_dates_valid'),
        CheckConstraint("warning_threshold_percentage > 0 AND warning_threshold_percentage <= 100", 
                       name='chk_budget_warning_threshold_range'),
        CheckConstraint("freeze_threshold_percentage > 0 AND freeze_threshold_percentage <= 100", 
                       name='chk_budget_freeze_threshold_range'),
        CheckConstraint("overspend_limit_percentage >= 0 AND overspend_limit_percentage <= 50", 
                       name='chk_budget_overspend_limit_range'),
        CheckConstraint("rollover_percentage >= 0 AND rollover_percentage <= 100", 
                       name='chk_budget_rollover_percentage_range'),
        Index('idx_budget_unit_type', 'unit_id', 'budget_type'),
        Index('idx_budget_period', 'fiscal_year', 'start_date', 'end_date'),
        Index('idx_budget_owner', 'budget_owner_id'),
        Index('idx_budget_category', 'category', 'subcategory'),
    )


class BudgetAllocation(Base):
    """
    Budget allocation model.
    Breaks down budget into specific allocations for detailed tracking.
    """
    __tablename__ = "budget_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent budget
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    
    # Allocation details
    allocation_code = Column(String(50), nullable=False, index=True)
    allocation_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Financial amounts
    allocated_amount = Column(Numeric(15, 2), nullable=False)
    committed_amount = Column(Numeric(15, 2), default=0)
    spent_amount = Column(Numeric(15, 2), default=0)
    available_amount = Column(Numeric(15, 2), nullable=False)
    
    # Categorization
    category = Column(String(100))
    subcategory = Column(String(100))
    account_code = Column(String(50))
    project_code = Column(String(50))
    
    # Allocation owner
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Controls
    is_active = Column(Boolean, default=True, nullable=False)
    can_overspend = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=True)
    approval_threshold = Column(Numeric(15, 2))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    budget = relationship("Budget", back_populates="allocations")
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints and indexes
    __table_args__ = (
        # Unique allocation code within budget
        Index('idx_budget_allocation_code', 'budget_id', 'allocation_code', unique=True),
        CheckConstraint("allocated_amount > 0", name='chk_allocation_amount_positive'),
        CheckConstraint("committed_amount >= 0", name='chk_allocation_committed_non_negative'),
        CheckConstraint("spent_amount >= 0", name='chk_allocation_spent_non_negative'),
        CheckConstraint("available_amount >= 0", name='chk_allocation_available_non_negative'),
        Index('idx_budget_allocation_owner', 'owner_id'),
        Index('idx_budget_allocation_category', 'category', 'subcategory'),
    )


class BudgetTransaction(Base):
    """
    Budget transaction model.
    Records all budget impacts from procurement activities.
    """
    __tablename__ = "budget_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Budget reference
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    allocation_id = Column(UUID(as_uuid=True), ForeignKey("budget_allocations.id"))
    
    # Transaction identification
    transaction_number = Column(String(100), unique=True, nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)  # "commitment", "expenditure", "adjustment", "reversal"
    
    # Source document
    source_document_type = Column(String(50))  # "requisition", "purchase_order", "invoice", "adjustment"
    source_document_id = Column(UUID(as_uuid=True))
    source_document_number = Column(String(100))
    
    # Financial details
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(12, 6))
    base_amount = Column(Numeric(15, 2))  # Amount in budget currency
    
    # Transaction details
    description = Column(Text, nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    effective_date = Column(DateTime(timezone=True))
    
    # Categorization
    category = Column(String(100))
    account_code = Column(String(50))
    cost_center = Column(String(50))
    project_code = Column(String(50))
    
    # Status
    status = Column(String(50), default="active")  # "active", "reversed", "cancelled"
    is_committed = Column(Boolean, default=True)  # Whether this affects committed amount
    is_spent = Column(Boolean, default=False)     # Whether this affects spent amount
    
    # Reversal information
    reversed_by_transaction_id = Column(UUID(as_uuid=True), ForeignKey("budget_transactions.id"))
    reversal_reason = Column(Text)
    reversed_at = Column(DateTime(timezone=True))
    
    # Approval (for adjustments)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    budget = relationship("Budget", back_populates="transactions")
    allocation = relationship("BudgetAllocation")
    reversed_by_transaction = relationship("BudgetTransaction", remote_side=[id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("amount != 0", name='chk_budget_transaction_amount_non_zero'),
        CheckConstraint("exchange_rate IS NULL OR exchange_rate > 0", name='chk_budget_transaction_exchange_rate'),
        CheckConstraint("transaction_type IN ('commitment', 'expenditure', 'adjustment', 'reversal')", 
                       name='chk_budget_transaction_type_valid'),
        CheckConstraint("status IN ('active', 'reversed', 'cancelled')", name='chk_budget_transaction_status_valid'),
        Index('idx_budget_transaction_date', 'transaction_date'),
        Index('idx_budget_transaction_source', 'source_document_type', 'source_document_id'),
        Index('idx_budget_transaction_type', 'transaction_type'),
        Index('idx_budget_transaction_category', 'category'),
    )


class ApprovalWorkflow(Base):
    """
    Approval workflow definition model.
    Defines the approval process for different types of procurement.
    """
    __tablename__ = "approval_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Workflow identification
    workflow_name = Column(String(200), nullable=False)
    workflow_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Multi-tenant
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False, index=True)
    
    # Workflow scope
    document_type = Column(String(50), nullable=False)  # "requisition", "purchase_order", "budget_adjustment"
    category = Column(String(100))  # Category this workflow applies to
    department = Column(String(100))  # Department this workflow applies to
    
    # Trigger conditions
    amount_threshold_min = Column(Numeric(15, 2), default=0)
    amount_threshold_max = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    
    # Workflow settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False)
    parallel_approval = Column(Boolean, default=False)  # All levels at once vs sequential
    timeout_hours = Column(Integer, default=72)  # Escalation timeout
    
    # Escalation settings
    escalation_enabled = Column(Boolean, default=True)
    escalation_after_hours = Column(Integer, default=24)
    max_escalation_levels = Column(Integer, default=2)
    
    # Priority settings
    priority_levels = Column(JSONB)  # Different approval rules for different priorities
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Status
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    unit = relationship("Unit")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Child relationships
    levels = relationship("ApprovalLevel", back_populates="workflow", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("amount_threshold_min >= 0", name='chk_workflow_min_threshold'),
        CheckConstraint("amount_threshold_max IS NULL OR amount_threshold_max > amount_threshold_min", 
                       name='chk_workflow_threshold_range'),
        CheckConstraint("timeout_hours > 0", name='chk_workflow_timeout_positive'),
        CheckConstraint("escalation_after_hours > 0", name='chk_workflow_escalation_time_positive'),
        CheckConstraint("max_escalation_levels >= 0", name='chk_workflow_max_escalation_levels'),
        Index('idx_workflow_unit_type', 'unit_id', 'document_type'),
        Index('idx_workflow_thresholds', 'amount_threshold_min', 'amount_threshold_max'),
        Index('idx_workflow_category', 'category'),
    )


class ApprovalLevel(Base):
    """
    Individual approval levels within a workflow.
    Defines who needs to approve at each level.
    """
    __tablename__ = "approval_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent workflow
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False, index=True)
    
    # Level details
    level_number = Column(Integer, nullable=False)
    level_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Approval requirements
    approval_type = Column(String(50), nullable=False)  # "role", "user", "any_of_role", "all_of_role"
    required_role = Column(String(50))  # If approval_type is role-based
    required_users = Column(JSONB)  # List of specific user IDs
    approvers_required = Column(Integer, default=1)  # Number of approvals needed
    
    # Conditions
    conditions = Column(JSONB)  # Additional conditions for this level
    amount_threshold = Column(Numeric(15, 2))  # Amount above which this level is required
    
    # Delegation settings
    delegation_allowed = Column(Boolean, default=True)
    delegation_restrictions = Column(JSONB)  # Who can delegate to whom
    
    # Timeout and escalation
    timeout_hours = Column(Integer, default=24)
    escalation_enabled = Column(Boolean, default=True)
    escalation_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    escalation_to_role = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="levels")
    escalation_user = relationship("User", foreign_keys=[escalation_to_user_id])
    
    # Constraints and indexes
    __table_args__ = (
        # Unique level numbers within workflow
        Index('idx_approval_level_workflow', 'workflow_id', 'level_number', unique=True),
        CheckConstraint("level_number > 0", name='chk_approval_level_number_positive'),
        CheckConstraint("approvers_required > 0", name='chk_approval_level_approvers_positive'),
        CheckConstraint("timeout_hours > 0", name='chk_approval_level_timeout_positive'),
        CheckConstraint("amount_threshold IS NULL OR amount_threshold >= 0", 
                       name='chk_approval_level_threshold'),
        CheckConstraint("approval_type IN ('role', 'user', 'any_of_role', 'all_of_role')", 
                       name='chk_approval_level_type_valid'),
        Index('idx_approval_level_role', 'required_role'),
        Index('idx_approval_level_threshold', 'amount_threshold'),
    )


class ApprovalRequest(Base):
    """
    Individual approval requests generated by the workflow engine.
    Tracks approval status for each level of each document.
    """
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request identification
    request_number = Column(String(100), unique=True, nullable=False, index=True)
    
    # Source document
    document_type = Column(String(50), nullable=False)  # "requisition", "purchase_order", "budget_adjustment"
    document_id = Column(UUID(as_uuid=True), nullable=False)
    document_number = Column(String(100))
    
    # Workflow reference
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False)
    level_id = Column(UUID(as_uuid=True), ForeignKey("approval_levels.id"), nullable=False)
    level_number = Column(Integer, nullable=False)
    
    # Approval assignment
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to_role = Column(String(50))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Request details
    amount = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    priority = Column(String(20), default="medium")
    
    # Status
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    
    # Decision
    decision_date = Column(DateTime(timezone=True))
    decision_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    decision_comments = Column(Text)
    conditions = Column(Text)  # Approval conditions
    
    # Timeouts and escalation
    due_date = Column(DateTime(timezone=True))
    escalated_at = Column(DateTime(timezone=True))
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    escalation_reason = Column(Text)
    
    # Delegation
    delegated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    delegation_reason = Column(Text)
    delegation_date = Column(DateTime(timezone=True))
    
    # Reminders and notifications
    reminder_sent_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime(timezone=True))
    escalation_reminder_sent = Column(Boolean, default=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    workflow = relationship("ApprovalWorkflow")
    level = relationship("ApprovalLevel")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    decision_by_user = relationship("User", foreign_keys=[decision_by])
    escalated_to_user = relationship("User", foreign_keys=[escalated_to])
    delegated_by_user = relationship("User", foreign_keys=[delegated_by])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("amount IS NULL OR amount >= 0", name='chk_approval_request_amount'),
        CheckConstraint("level_number > 0", name='chk_approval_request_level_positive'),
        CheckConstraint("reminder_sent_count >= 0", name='chk_approval_request_reminders'),
        Index('idx_approval_request_document', 'document_type', 'document_id'),
        Index('idx_approval_request_assignee', 'assigned_to_user_id'),
        Index('idx_approval_request_status', 'status'),
        Index('idx_approval_request_due_date', 'due_date'),
        Index('idx_approval_request_workflow', 'workflow_id'),
        Index('idx_approval_request_level', 'level_id'),
    )
