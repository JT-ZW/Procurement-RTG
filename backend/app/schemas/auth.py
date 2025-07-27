"""
Pydantic schemas for authentication and authorization.
Handles login, registration, token management, and password operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator, Field


# Token and Authentication Schemas

class Token(BaseModel):
    """Response schema for authentication token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # Token expiration in seconds
    user: "UserResponse"  # Forward reference
    units: List["UnitBasic"] = []  # User's accessible units
    permissions: Optional[Dict[str, Any]] = None  # User permissions summary
    
    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: Optional[str] = None  # Subject (user ID)
    exp: Optional[int] = None  # Expiration time
    iat: Optional[int] = None  # Issued at time
    jti: Optional[str] = None  # JWT ID
    type: str = "access"  # Token type
    
    class Config:
        from_attributes = True


class RefreshToken(BaseModel):
    """Refresh token request schema."""
    refresh_token: str
    
    class Config:
        from_attributes = True


# Login and Authentication Schemas

class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)
    remember_me: bool = False
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@hotel.com",
                "password": "securepassword123",
                "remember_me": False
            }
        }


class UserLoginResponse(BaseModel):
    """User login response schema."""
    success: bool = True
    message: str = "Login successful"
    token: Token
    session_id: Optional[str] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Registration and User Creation Schemas

class UserCreate(BaseModel):
    """Schema for creating new users."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=200)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(superuser|procurement_admin|unit_manager|store_manager|store_staff|supplier_user)$")
    
    # Optional fields
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    
    # Employee information
    employee_id: Optional[str] = Field(None, max_length=50)
    manager_id: Optional[UUID] = None
    cost_center: Optional[str] = Field(None, max_length=50)
    
    # Unit assignments
    unit_assignments: Optional[List["UserUnitAssignmentCreate"]] = []
    
    # Preferences
    language: str = Field("en", max_length=10)
    timezone: str = Field("UTC", max_length=50)
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, lowercase, and digit
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if v and not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError('Username must be alphanumeric (with optional underscores and dots)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@hotel.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
                "role": "store_manager",
                "title": "Store Manager",
                "department": "Food & Beverage",
                "phone": "+1-555-0123",
                "employee_id": "EMP001",
                "language": "en",
                "timezone": "America/New_York"
            }
        }


class UserRegister(UserCreate):
    """Schema for user self-registration (if enabled)."""
    terms_accepted: bool = True
    privacy_policy_accepted: bool = True
    
    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v
    
    @validator('privacy_policy_accepted')
    def privacy_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Privacy policy must be accepted')
        return v


# Password Management Schemas

class PasswordChange(BaseModel):
    """Schema for changing password (authenticated user)."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=200)
    confirm_password: str = Field(..., min_length=8, max_length=200)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "NewSecurePass456",
                "confirm_password": "NewSecurePass456"
            }
        }


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset."""
    email: EmailStr
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@hotel.com"
            }
        }


class PasswordReset(BaseModel):
    """Schema for resetting password with token."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=200)
    confirm_password: str = Field(..., min_length=8, max_length=200)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123"
            }
        }


class PasswordResetResponse(BaseModel):
    """Response schema for password reset operations."""
    success: bool = True
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Password has been reset successfully"
            }
        }


# Two-Factor Authentication Schemas

class TwoFactorSetup(BaseModel):
    """Schema for setting up two-factor authentication."""
    secret: str
    qr_code_url: str
    backup_codes: List[str]
    
    class Config:
        from_attributes = True


class TwoFactorVerify(BaseModel):
    """Schema for verifying two-factor authentication code."""
    code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "123456"
            }
        }


class TwoFactorDisable(BaseModel):
    """Schema for disabling two-factor authentication."""
    password: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "password": "currentpassword",
                "code": "123456"
            }
        }


# User Response Schemas (used in Token response)

class UnitBasic(BaseModel):
    """Basic unit information for token response."""
    id: UUID
    name: str
    code: str = Field(..., alias="unit_code")
    city: Optional[str] = None
    status: str
    
    class Config:
        from_attributes = True
        populate_by_name = True


class UserUnitAssignmentResponse(BaseModel):
    """User unit assignment information."""
    unit_id: UUID
    unit: UnitBasic
    role: str
    is_primary_unit: bool = False
    can_approve_orders: bool = False
    approval_limit: float = 0.0
    assigned_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User information for API responses."""
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    role: str
    is_superuser: bool = False
    is_active: bool = True
    
    # Contact information
    phone: Optional[str] = None
    mobile: Optional[str] = None
    
    # Employment information
    employee_id: Optional[str] = None
    manager_id: Optional[UUID] = None
    
    # Preferences
    language: str = "en"
    timezone: str = "UTC"
    
    # Status information
    last_login_at: Optional[datetime] = None
    email_verified: bool = False
    two_factor_enabled: bool = False
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Unit assignments (optional - included when needed)
    unit_assignments: Optional[List[UserUnitAssignmentResponse]] = []
    
    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        if v:
            return v
        first_name = values.get('first_name', '')
        last_name = values.get('last_name', '')
        return f"{first_name} {last_name}".strip()
    
    class Config:
        from_attributes = True


# Unit Assignment Schemas

class UserUnitAssignmentCreate(BaseModel):
    """Schema for creating user unit assignments."""
    unit_id: UUID
    role: str = Field(..., pattern="^(unit_manager|store_manager|store_staff|supplier_liaison)$")
    is_primary_unit: bool = False
    can_approve_orders: bool = False
    can_manage_inventory: bool = True
    can_manage_suppliers: bool = False
    can_view_reports: bool = True
    approval_limit: float = Field(0.0, ge=0)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "unit_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "store_manager",
                "is_primary_unit": True,
                "can_approve_orders": True,
                "approval_limit": 5000.0
            }
        }


# Session Management Schemas

class SessionInfo(BaseModel):
    """User session information."""
    session_id: str
    ip_address: str
    user_agent: Optional[str] = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_current: bool = False
    
    class Config:
        from_attributes = True


class SessionList(BaseModel):
    """List of user sessions."""
    sessions: List[SessionInfo]
    current_session_id: Optional[str] = None
    
    class Config:
        from_attributes = True


# Account Management Schemas

class AccountStatus(BaseModel):
    """User account status information."""
    is_active: bool
    is_locked: bool = False
    locked_until: Optional[datetime] = None
    failed_login_attempts: int = 0
    last_login_at: Optional[datetime] = None
    email_verified: bool = False
    two_factor_enabled: bool = False
    password_expires_at: Optional[datetime] = None
    must_change_password: bool = False
    
    class Config:
        from_attributes = True


class AccountActivation(BaseModel):
    """Schema for account activation."""
    token: str
    password: str = Field(..., min_length=8, max_length=200)
    terms_accepted: bool = True
    privacy_policy_accepted: bool = True
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v


# API Response Schemas

class AuthResponse(BaseModel):
    """Generic authentication response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Authentication failed",
                "error_code": "INVALID_CREDENTIALS",
                "details": {"field": "password", "issue": "incorrect"}
            }
        }


# Permissions and Roles Schemas

class RolePermissions(BaseModel):
    """Role permissions information."""
    role: str
    permissions: List[str]
    description: str
    can_assign_roles: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "unit_manager",
                "permissions": ["manage_inventory", "approve_orders", "view_reports"],
                "description": "Hotel unit manager with full operational control",
                "can_assign_roles": ["store_manager", "store_staff"]
            }
        }


class AvailableRoles(BaseModel):
    """Available roles for user assignment."""
    available_roles: List[str]
    role_descriptions: Dict[str, str]
    current_user_role: str
    
    class Config:
        from_attributes = True


# Forward reference updates
Token.model_rebuild()
UserResponse.model_rebuild()