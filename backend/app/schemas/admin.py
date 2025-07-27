"""
Admin Dashboard Schemas
Pydantic models for admin-specific operations and dashboard data.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from uuid import UUID

from app.schemas.user import UserRole


class UnitStats(BaseModel):
    """Statistics for a specific unit."""
    unit_id: str
    unit_name: str
    unit_code: str
    products_count: int
    suppliers_count: int
    users_count: int
    low_stock_items: Optional[int] = 0
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics for the current user's accessible units."""
    period_days: int
    units: List[UnitStats]
    total_accessible_units: int

    class Config:
        from_attributes = True


class SystemOverview(BaseModel):
    """System-wide overview statistics (superuser only)."""
    total_units: int
    active_units: int
    total_users: int
    active_users: int
    total_products: int
    total_suppliers: int
    total_assignments: int
    new_users_this_week: int

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics across the system."""
    total_users: int
    active_users: int
    role_distribution: Dict[str, int]
    new_users_this_week: int
    new_users_this_month: int
    active_sessions: int

    class Config:
        from_attributes = True


class UnitAssignmentCreate(BaseModel):
    """Schema for creating user-unit assignments."""
    unit_id: UUID
    role: UserRole
    is_primary_unit: bool = False
    can_approve_orders: bool = False
    approval_limit: Optional[float] = None


class AdminUserCreate(BaseModel):
    """Schema for creating users through admin interface."""
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    title: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.STORE_STAFF
    is_superuser: bool = False
    is_active: bool = True
    unit_assignments: Optional[List[UnitAssignmentCreate]] = []

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v


class AdminUserUpdate(BaseModel):
    """Schema for updating users through admin interface."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UnitConfigUpdate(BaseModel):
    """Schema for updating unit configuration."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    location_postal_code: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    tax_rate: Optional[float] = None
    settings: Optional[Dict[str, Any]] = None

    @validator('tax_rate')
    def validate_tax_rate(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Tax rate must be between 0 and 1')
        return v


class SystemSettings(BaseModel):
    """System-wide settings and configuration."""
    system_name: str
    version: str
    multi_tenant_enabled: bool
    total_units: int
    maintenance_mode: bool = False
    registration_enabled: bool = True
    password_policy: Dict[str, Union[int, bool]]

    class Config:
        from_attributes = True


class ActivityLog(BaseModel):
    """Activity log entry for audit trail."""
    id: UUID
    user_id: UUID
    user_name: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AdminActivityLogQuery(BaseModel):
    """Query parameters for activity log filtering."""
    user_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

    @validator('limit')
    def validate_limit(cls, v):
        if v > 1000:
            raise ValueError('Limit cannot exceed 1000')
        return v


class QuickAction(BaseModel):
    """Quick action item for admin dashboard."""
    id: str
    title: str
    description: str
    icon: str
    action_type: str  # 'navigation', 'modal', 'api_call'
    target: str  # URL, modal ID, or API endpoint
    requires_confirmation: bool = False
    permission_required: Optional[str] = None


class AlertItem(BaseModel):
    """Alert item for admin dashboard."""
    id: str
    title: str
    message: str
    type: str  # 'info', 'warning', 'error', 'success'
    priority: str  # 'low', 'medium', 'high', 'critical'
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None
    action_required: bool = False
    action_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class DashboardConfig(BaseModel):
    """Configuration for admin dashboard display."""
    widgets_enabled: List[str] = [
        "system_overview",
        "unit_stats",
        "recent_activity",
        "alerts",
        "quick_actions"
    ]
    default_period_days: int = 30
    refresh_interval_seconds: int = 300
    show_inactive_units: bool = False
    max_recent_activities: int = 10
    max_alerts: int = 5


class UserSummary(BaseModel):
    """Summary information about a user for admin views."""
    id: UUID
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    units_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class UnitSummary(BaseModel):
    """Summary information about a unit for admin views."""
    id: UUID
    name: str
    unit_code: str
    is_active: bool
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    manager_name: Optional[str] = None
    users_count: int
    products_count: int
    suppliers_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SystemHealthCheck(BaseModel):
    """System health check result."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: datetime
    checks: Dict[str, Dict[str, Union[str, bool, int, float]]]
    overall_score: float  # 0.0 to 1.0
    recommendations: List[str] = []

    class Config:
        from_attributes = True
