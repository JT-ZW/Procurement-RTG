"""
Security Configuration
Authentication, authorization, and security utilities for the Procurement System.
Handles JWT tokens, password hashing, role-based access, and multi-tenant security.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any, List
import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import string

from app.core.config import settings
from app.core.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# =====================================================
# PASSWORD HASHING
# =====================================================

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Good balance of security and performance
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password from database
    
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password to hash
    
    Returns:
        str: Hashed password ready for database storage
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength according to security policy.
    
    Args:
        password: Password to validate
    
    Returns:
        tuple: (is_valid: bool, issues: List[str])
    
    Example:
        is_valid, issues = validate_password_strength("weak")
        if not is_valid:
            raise ValidationError(f"Password issues: {', '.join(issues)}")
    """
    issues = []
    
    # Length check
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if len(password) > 128:
        issues.append("Password must be less than 128 characters long")
    
    # Character requirements
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        issues.append("Password must contain at least one special character")
    
    # Check for common patterns
    if password.lower() in ["password", "123456", "qwerty", "admin"]:
        issues.append("Password is too common")
    
    return len(issues) == 0, issues

# =====================================================
# JWT TOKEN MANAGEMENT
# =====================================================

def create_access_token(
    subject: Union[str, UUID], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Custom expiration time (optional)
        additional_claims: Additional claims to include in token
    
    Returns:
        str: Encoded JWT token
    
    Example:
        token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role, "units": user_units}
        )
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Standard JWT claims
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "access",
        "iss": settings.APP_NAME  # Issuer
    }
    
    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        logger.debug(f"Created access token for subject: {str(subject)[:8]}...")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise


def create_refresh_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Custom expiration time (optional)
    
    Returns:
        str: Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "refresh",
        "iss": settings.APP_NAME
    }
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        logger.debug(f"Created refresh token for subject: {str(subject)[:8]}...")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create refresh token: {e}")
        raise


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')
    
    Returns:
        dict: Token payload if valid, None if invalid
    
    Example:
        payload = verify_token(token, "access")
        if payload:
            user_id = payload.get("sub")
    """
    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
            return None
        
        # Verify issuer
        if payload.get("iss") != settings.APP_NAME:
            logger.warning(f"Invalid token issuer: {payload.get('iss')}")
            return None
        
        # Check if token is expired (jwt library should handle this, but double-check)
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            logger.debug("Token has expired")
            return None
        
        logger.debug(f"Token verified successfully for subject: {payload.get('sub', 'unknown')[:8]}...")
        return payload
        
    except JWTError as e:
        logger.debug(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

# =====================================================
# AUTHENTICATION DEPENDENCIES
# =====================================================

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UUID:
    """
    Extract and validate user ID from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request header
    
    Returns:
        UUID: Verified user ID
    
    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    # Check if credentials were provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify the token
        payload = verify_token(credentials.credentials, "access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user ID
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert to UUID
        try:
            user_id = UUID(user_id_str)
            return user_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user from database.
    
    Args:
        user_id: User ID extracted from JWT token
        db: Database session
    
    Returns:
        User: Complete user object from database
    
    Raises:
        HTTPException: If user not found or inactive
    """
    try:
        # Import User model here to avoid circular imports
        # This will be available once we create the models
        from app.models.user import User
        
        # Query user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        # Check if user exists
        if not user:
            logger.warning(f"User not found in database: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is active
        if user.status != "active":
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login time (don't wait for commit)
        user.last_login_at = datetime.utcnow()
        # Note: This will be committed when the request completes
        
        logger.debug(f"User authenticated successfully: {user.email}")
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error"
        )


# Alias for backward compatibility
async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Get current active user (alias for get_current_user).
    
    Args:
        current_user: Current user from get_current_user dependency
    
    Returns:
        User: Active user object
    """
    return current_user


async def get_current_active_superuser(
    current_user = Depends(get_current_user)
):
    """
    Get current active superuser.
    
    Args:
        current_user: Current user from get_current_user dependency
    
    Returns:
        User: Active superuser object
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser access required."
        )
    return current_user

# =====================================================
# ROLE-BASED ACCESS CONTROL
# =====================================================

class RoleChecker:
    """
    Role-based access control dependency factory.
    
    Creates FastAPI dependencies that check user roles.
    
    Usage:
        # Single role
        admin_only = RoleChecker(["super_admin"])
        
        # Multiple roles
        managers = RoleChecker(["super_admin", "procurement_admin", "unit_manager"])
        
        @app.get("/admin-endpoint")
        async def admin_endpoint(user = Depends(admin_only)):
            return {"message": "Admin access granted"}
    """
    
    def __init__(self, allowed_roles: List[str]):
        """
        Initialize role checker.
        
        Args:
            allowed_roles: List of roles that are allowed access
        """
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user = Depends(get_current_user)):
        """
        Check if current user has required role.
        
        Args:
            current_user: Current authenticated user
        
        Returns:
            User: User object if role check passes
        
        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            logger.warning(
                f"Role access denied. User {current_user.email} "
                f"has role '{current_user.role}', required: {self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        
        logger.debug(f"Role access granted for {current_user.email} ({current_user.role})")
        return current_user


# Pre-defined role checkers for common access patterns
require_super_admin = RoleChecker(["super_admin"])
require_admin = RoleChecker(["super_admin", "procurement_admin"])
require_manager = RoleChecker(["super_admin", "procurement_admin", "unit_manager"])
require_store_manager = RoleChecker([
    "super_admin", "procurement_admin", "unit_manager", "store_manager"
])
require_staff = RoleChecker([
    "super_admin", "procurement_admin", "unit_manager", "store_manager", "store_staff"
])

# =====================================================
# MULTI-TENANT ACCESS CONTROL
# =====================================================

async def get_user_accessible_units(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[UUID]:
    """
    Get list of unit IDs that the current user has access to.
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List[UUID]: List of unit IDs the user can access
    
    Note:
        Super admins and procurement admins get access to all active units.
        Other users get access based on their unit assignments.
    """
    try:
        # Super admins and procurement admins have access to all units
        if current_user.role in ["super_admin", "procurement_admin"]:
            from app.models.unit import Unit
            result = await db.execute(
                select(Unit.id).where(Unit.is_active == True)
            )
            unit_ids = [row[0] for row in result.fetchall()]
            logger.debug(f"Admin user {current_user.email} has access to all {len(unit_ids)} units")
            return unit_ids
        
        # Other users have access based on their assignments
        from app.models.user import UserUnitAssignment
        result = await db.execute(
            select(UserUnitAssignment.unit_id)
            .where(UserUnitAssignment.user_id == current_user.id)
        )
        unit_ids = [row[0] for row in result.fetchall()]
        logger.debug(f"User {current_user.email} has access to {len(unit_ids)} units")
        return unit_ids
        
    except Exception as e:
        logger.error(f"Error getting user accessible units: {e}")
        # Return empty list on error (no access)
        return []


class UnitAccessChecker:
    """
    Multi-tenant access control dependency.
    Validates that user has access to a specific unit.
    
    Usage:
        check_unit_access = UnitAccessChecker()
        
        @app.get("/units/{unit_id}/products")
        async def get_unit_products(
            unit_id: UUID,
            user = Depends(check_unit_access)
        ):
            # User has verified access to unit_id
            return {"products": "..."}
    """
    
    def __init__(self):
        pass
    
    async def __call__(
        self,
        unit_id: UUID,
        current_user = Depends(get_current_user),
        accessible_units: List[UUID] = Depends(get_user_accessible_units)
    ):
        """
        Check if user has access to the specified unit.
        
        Args:
            unit_id: Unit ID from path parameter
            current_user: Current authenticated user
            accessible_units: Units the user has access to
        
        Returns:
            User: User object if access check passes
        
        Raises:
            HTTPException: If user doesn't have access to the unit
        """
        if unit_id not in accessible_units:
            logger.warning(
                f"Unit access denied. User {current_user.email} "
                f"attempted to access unit {unit_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this unit"
            )
        
        logger.debug(f"Unit access granted for {current_user.email} to unit {unit_id}")
        return current_user

# =====================================================
# SECURITY UTILITIES
# =====================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token to generate
    
    Returns:
        str: Secure random token
    
    Usage:
        reset_token = generate_secure_token(64)
        api_key = generate_secure_token(32)
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask sensitive data for logging and display.
    
    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to show at the end
        mask_char: Character to use for masking
    
    Returns:
        str: Masked data string
    
    Example:
        masked_email = mask_sensitive_data("user@example.com", 4)
        # Returns: "***********@.com"
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request, handling proxies.
    
    Args:
        request: FastAPI request object
    
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"


def validate_email_format(email: str) -> bool:
    """
    Basic email format validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if email format is valid
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.match(pattern, email) is not None

# =====================================================
# SECURITY HEADERS AND MIDDLEWARE UTILITIES
# =====================================================

def get_security_headers() -> dict:
    """
    Get security headers to add to responses.
    
    Returns:
        dict: Security headers for HTTP responses
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    
    # Add HSTS header in production
    if not settings.DEBUG:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return headers


def create_login_response(user, access_token: str, refresh_token: str) -> dict:
    """
    Create standardized login response.
    
    Args:
        user: User object
        access_token: JWT access token
        refresh_token: JWT refresh token
    
    Returns:
        dict: Login response data
    """
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "status": user.status
        }
    }

# =====================================================
# TOKEN BLACKLIST (for logout functionality)
# =====================================================

# In-memory token blacklist (in production, use Redis)
_token_blacklist = set()

def blacklist_token(token: str):
    """
    Add token to blacklist (for logout).
    
    Args:
        token: JWT token to blacklist
    
    Note:
        In production, this should use Redis or database storage.
    """
    _token_blacklist.add(token)
    logger.debug(f"Token blacklisted: {token[:20]}...")


def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted.
    
    Args:
        token: JWT token to check
    
    Returns:
        bool: True if token is blacklisted
    """
    return token in _token_blacklist


# Export commonly used items
__all__ = [
    # Password functions
    "verify_password",
    "get_password_hash", 
    "validate_password_strength",
    
    # JWT functions
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    
    # Authentication dependencies
    "get_current_user",
    "get_current_user_id",
    "get_current_active_user",
    
    # Role-based access control
    "RoleChecker",
    "require_super_admin",
    "require_admin",
    "require_manager",
    "require_store_manager",
    "require_staff",
    
    # Multi-tenant access control
    "get_user_accessible_units",
    "UnitAccessChecker",
    
    # Utilities
    "generate_secure_token",
    "mask_sensitive_data",
    "get_client_ip",
    "validate_email_format",
    "get_security_headers",
    "create_login_response",
    "blacklist_token",
    "is_token_blacklisted"
]