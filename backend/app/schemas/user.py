from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime
from uuid import UUID
from enum import Enum
import re


class UserRole(str, Enum):
    """User roles in the system"""
    SUPERUSER = "superuser"
    PROCUREMENT_ADMIN = "procurement_admin"
    UNIT_MANAGER = "unit_manager"
    STORE_MANAGER = "store_manager"
    STORE_STAFF = "store_staff"
    SUPPLIER_USER = "supplier_user"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=2, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="User's last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    employee_id: Optional[str] = Field(None, max_length=20, description="Employee ID")
    department: Optional[str] = Field(None, max_length=50, description="Department/Division")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    is_active: bool = Field(default=True, description="Whether user account is active")
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Ensure names are properly formatted"""
        if v:
            return v.strip().title()
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Basic phone number validation"""
        if v:
            # Remove all non-digits
            phone_digits = re.sub(r'\D', '', v)
            if len(phone_digits) < 7:
                raise ValueError('Phone number must contain at least 7 digits')
        return v
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        """Validate employee ID format"""
        if v:
            return v.strip().upper()
        return v


class UserPersonalInfo(BaseModel):
    """Extended personal information"""
    middle_name: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[datetime] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    timezone: str = Field(default="UTC", description="User's preferred timezone")


class UserPreferences(BaseModel):
    """User preferences and settings"""
    language: str = Field(default="en", max_length=5, description="Preferred language")
    date_format: str = Field(default="YYYY-MM-DD", description="Preferred date format")
    currency_display: str = Field(default="USD", max_length=3, description="Preferred currency")
    notifications_email: bool = Field(default=True, description="Email notifications enabled")
    notifications_sms: bool = Field(default=False, description="SMS notifications enabled")
    dashboard_layout: Optional[Dict[str, Any]] = Field(None, description="Dashboard customization")
    theme: str = Field(default="light", pattern=r'^(light|dark|auto)$', description="UI theme preference")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    role: UserRole = Field(..., description="Primary user role")
    assigned_units: Optional[List[UUID]] = Field(default=[], description="Units assigned to user")
    supplier_id: Optional[UUID] = Field(None, description="Associated supplier (for supplier users)")
    personal_info: Optional[UserPersonalInfo] = None
    preferences: Optional[UserPreferences] = None
    send_welcome_email: bool = Field(default=True, description="Send welcome email to user")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    employee_id: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    assigned_units: Optional[List[UUID]] = None
    personal_info: Optional[UserPersonalInfo] = None
    preferences: Optional[UserPreferences] = None
    
    @validator('first_name', 'last_name')
    def validate_names_update(cls, v):
        """Ensure names are properly formatted when updating"""
        if v:
            return v.strip().title()
        return v


class UserPasswordUpdate(BaseModel):
    """Schema for password updates"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserInDBBase(UserBase):
    """Base schema for user data from database"""
    id: UUID
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_attempts: int = 0
    password_changed_at: Optional[datetime] = None
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    personal_info: Optional[UserPersonalInfo] = None
    preferences: Optional[UserPreferences] = None
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Complete user schema for API responses (no sensitive data)"""
    assigned_units: List[UUID] = []
    permissions: List[str] = []
    supplier_id: Optional[UUID] = None


class UserInDB(UserInDBBase):
    """User schema as stored in database (includes sensitive fields)"""
    hashed_password: str
    assigned_units: List[UUID] = []
    permissions: List[str] = []
    supplier_id: Optional[UUID] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    email_verification_token: Optional[str] = None


class UserList(BaseModel):
    """Schema for listing users with pagination"""
    users: List[User]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class UserProfile(BaseModel):
    """Detailed user profile"""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str]
    employee_id: Optional[str]
    department: Optional[str]
    job_title: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    assigned_units: List[Dict[str, Any]] = []  # Unit details
    permissions: List[str] = []
    personal_info: Optional[UserPersonalInfo] = None
    preferences: Optional[UserPreferences] = None
    stats: Optional[Dict[str, Any]] = None  # User activity stats


class UserSummary(BaseModel):
    """Brief user summary for listings"""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    status: UserStatus
    is_active: bool
    department: Optional[str]
    job_title: Optional[str]
    last_login: Optional[datetime]
    assigned_units_count: int


class UserPermission(BaseModel):
    """User permission schema"""
    user_id: UUID
    permission: str
    resource: Optional[str] = None
    unit_id: Optional[UUID] = None
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class UserSession(BaseModel):
    """User session information"""
    user_id: UUID
    session_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    current_unit_id: Optional[UUID]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True


class UserActivityLog(BaseModel):
    """User activity logging"""
    user_id: UUID
    action: str
    resource: Optional[str] = None
    resource_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    success: bool = True


class UserInvitation(BaseModel):
    """Schema for inviting new users"""
    email: EmailStr
    role: UserRole
    assigned_units: List[UUID] = []
    invited_by: UUID
    invitation_message: Optional[str] = Field(None, max_length=500)
    expires_in_days: int = Field(default=7, ge=1, le=30)


class UserInvitationResponse(BaseModel):
    """Response to user invitation"""
    invitation_id: UUID
    email: EmailStr
    role: UserRole
    assigned_units: List[UUID]
    invited_by: Dict[str, str]  # Basic info about inviter
    created_at: datetime
    expires_at: datetime
    status: str  # pending, accepted, expired, revoked


class UserBulkOperation(BaseModel):
    """Schema for bulk operations on users"""
    user_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., pattern=r'^(activate|deactivate|assign_units|remove_units|change_role)$')
    data: Optional[Dict[str, Any]] = None


class UserValidationError(BaseModel):
    """Schema for user validation errors"""
    field: str
    message: str
    code: str


class UserOperationResult(BaseModel):
    """Result of user operations"""
    success: bool
    message: str
    user_id: Optional[UUID] = None
    errors: Optional[List[UserValidationError]] = None


class UserStats(BaseModel):
    """User statistics and metrics"""
    user_id: UUID
    total_logins: int
    last_login: Optional[datetime]
    total_requisitions: int
    total_orders_processed: int
    average_session_duration: Optional[float]  # in minutes
    most_active_unit: Optional[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]
    permissions_summary: Dict[str, int]


class UserExport(BaseModel):
    """Schema for user data export"""
    users: List[UserProfile]
    export_date: datetime
    exported_by: UUID
    filters_applied: Dict[str, Any]
    total_records: int


# Response schema aliases for backward compatibility
UserResponse = User  # Main response schema for API endpoints
UserListResponse = UserList  # For list endpoints
UserProfileResponse = UserProfile  # For profile endpoints

# Additional schemas for API compatibility
UserProfileUpdate = UserUpdate  # Alias for profile updates
UserRoleUpdate = UserUpdate  # Alias for role updates  
UserStatusUpdate = UserUpdate  # Alias for status updates
UserSearchParams = UserBase  # Alias for search parameters
UserStatsResponse = UserStats  # Alias for stats response
UserActivityResponse = UserActivityLog  # Alias for activity response