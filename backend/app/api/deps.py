"""
API Dependencies
Common dependencies shared across API endpoints for the Procurement System.
Includes pagination, filtering, validation, and business logic dependencies.
"""

from typing import Optional, List, Any, Dict, Union, Tuple
from uuid import UUID
import logging
from datetime import datetime, date

from fastapi import Depends, HTTPException, status, Query, Path, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, validator

# Import from our core modules
from app.core.database import get_db
from app.core.security import (
    get_current_user, 
    get_current_user_id,
    get_current_active_user, 
    get_current_active_superuser
)
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# =====================================================
# RE-EXPORT COMMON DEPENDENCIES FOR CONVENIENCE
# =====================================================

# Database dependency
GetDB = get_db

# Authentication dependencies
GetCurrentUser = get_current_user
GetCurrentUserId = get_current_user_id
GetCurrentActiveUser = get_current_active_user
GetCurrentActiveSuperuser = get_current_active_superuser

# For backward compatibility, also export without Get prefix
get_current_active_superuser = get_current_active_superuser


def get_current_unit(
    request: Request,
    current_user = Depends(get_current_user)
) -> Optional[UUID]:
    """
    Get current unit context from request headers or user's default unit.
    """
    from app.utils.multi_tenant import get_current_unit_context
    
    # Try to get unit from header first
    unit_header = request.headers.get("X-Current-Unit")
    if unit_header:
        try:
            return UUID(unit_header)
        except ValueError:
            pass
    
    # Fall back to user's default unit context
    return get_current_unit_context(current_user)

# Unit access checker
CheckUnitAccess = UnitAccessChecker()

# =====================================================
# PAGINATION DEPENDENCIES
# =====================================================

class PaginationParams(BaseModel):
    """
    Pagination parameters model.
    """
    page: int = 1
    size: int = 20
    total: Optional[int] = None
    
    @validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v
    
    @validator("size")
    def validate_size(cls, v):
        if v < 1:
            raise ValueError("Size must be >= 1")
        if v > settings.MAX_PAGE_SIZE:
            raise ValueError(f"Size must be <= {settings.MAX_PAGE_SIZE}")
        return v
    
    @property
    def offset(self) -> int:
        """Calculate offset for SQL queries."""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """Get limit for SQL queries."""
        return self.size


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE, 
        ge=1, 
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (max {settings.MAX_PAGE_SIZE})"
    )
) -> PaginationParams:
    """
    Extract pagination parameters from query string.
    
    Args:
        page: Page number (1-based)
        size: Items per page
    
    Returns:
        PaginationParams: Validated pagination parameters
    
    Usage:
        @app.get("/users/")
        async def get_users(pagination: PaginationParams = Depends(get_pagination_params)):
            offset = pagination.offset
            limit = pagination.limit
    """
    return PaginationParams(page=page, size=size)


class PaginatedResponse(BaseModel):
    """
    Standard paginated response model.
    """
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, items: List[Any], total: int, pagination: PaginationParams):
        """
        Create paginated response from items and pagination params.
        
        Args:
            items: List of items for current page
            total: Total number of items
            pagination: Pagination parameters
        
        Returns:
            PaginatedResponse: Formatted response
        """
        pages = (total + pagination.size - 1) // pagination.size  # Ceiling division
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )

# =====================================================
# SORTING DEPENDENCIES
# =====================================================

class SortParams(BaseModel):
    """
    Sorting parameters model.
    """
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


def get_sort_params(
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order: asc or desc")
) -> SortParams:
    """
    Extract sorting parameters from query string.
    
    Args:
        sort_by: Field name to sort by
        sort_order: Sort direction (asc/desc)
    
    Returns:
        SortParams: Validated sorting parameters
    
    Usage:
        @app.get("/products/")
        async def get_products(sort: SortParams = Depends(get_sort_params)):
            if sort.sort_by:
                # Apply sorting to query
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)

# =====================================================
# FILTERING DEPENDENCIES
# =====================================================

def get_date_range_filter(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
) -> Tuple[Optional[date], Optional[date]]:
    """
    Extract date range filter from query parameters.
    
    Args:
        start_date: Filter start date
        end_date: Filter end date
    
    Returns:
        Tuple[Optional[date], Optional[date]]: Date range tuple
    
    Raises:
        HTTPException: If date range is invalid
    
    Usage:
        @app.get("/orders/")
        async def get_orders(
            date_range: Tuple[Optional[date], Optional[date]] = Depends(get_date_range_filter)
        ):
            start_date, end_date = date_range
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )
    
    return start_date, end_date


def get_search_filter(
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search term")
) -> Optional[str]:
    """
    Extract and validate search term from query parameters.
    
    Args:
        search: Search term
    
    Returns:
        Optional[str]: Cleaned search term
    
    Usage:
        @app.get("/products/")
        async def search_products(search_term: Optional[str] = Depends(get_search_filter)):
            if search_term:
                # Apply search filter
    """
    if search:
        # Clean and validate search term
        search = search.strip()
        if len(search) == 0:
            return None
        
        # Basic sanitization - remove potentially dangerous characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        for char in dangerous_chars:
            if char in search.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid characters in search term"
                )
    
    return search


def get_status_filter(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status")
) -> Optional[str]:
    """
    Extract status filter from query parameters.
    
    Args:
        status_filter: Status to filter by
    
    Returns:
        Optional[str]: Status filter value
    """
    return status_filter

# =====================================================
# MULTI-TENANT DEPENDENCIES
# =====================================================

async def get_accessible_unit_filter(
    accessible_units: List[UUID] = Depends(get_user_accessible_units)
) -> List[UUID]:
    """
    Get accessible units for filtering queries.
    
    Args:
        accessible_units: Units the current user can access
    
    Returns:
        List[UUID]: Unit IDs for filtering
    
    Usage:
        @app.get("/stock/")
        async def get_stock(
            unit_filter: List[UUID] = Depends(get_accessible_unit_filter)
        ):
            # Query will be automatically filtered to accessible units
    """
    return accessible_units


async def validate_unit_access(
    unit_id: UUID = Path(..., description="Unit ID"),
    accessible_units: List[UUID] = Depends(get_user_accessible_units)
) -> UUID:
    """
    Validate that user has access to specified unit.
    
    Args:
        unit_id: Unit ID from path parameter
        accessible_units: Units the user has access to
    
    Returns:
        UUID: Validated unit ID
    
    Raises:
        HTTPException: If user doesn't have access to unit
    
    Usage:
        @app.get("/units/{unit_id}/products")
        async def get_unit_products(
            unit_id: UUID = Depends(validate_unit_access)
        ):
            # unit_id is validated for access
    """
    if unit_id not in accessible_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this unit"
        )
    return unit_id

# =====================================================
# VALIDATION DEPENDENCIES
# =====================================================

def validate_uuid_path(
    resource_id: UUID = Path(..., description="Resource UUID")
) -> UUID:
    """
    Validate UUID path parameter.
    
    Args:
        resource_id: UUID from path
    
    Returns:
        UUID: Validated UUID
    
    Usage:
        @app.get("/users/{user_id}")
        async def get_user(user_id: UUID = Depends(validate_uuid_path)):
            # user_id is guaranteed to be valid UUID
    """
    return resource_id


async def validate_resource_exists(
    resource_id: UUID,
    model_class,
    db: AsyncSession,
    error_message: str = "Resource not found"
) -> Any:
    """
    Generic function to validate that a resource exists.
    
    Args:
        resource_id: Resource UUID
        model_class: SQLAlchemy model class
        db: Database session
        error_message: Custom error message
    
    Returns:
        Any: The found resource
    
    Raises:
        HTTPException: If resource not found
    """
    result = await db.execute(
        select(model_class).where(model_class.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message
        )
    
    return resource


# Factory functions for specific resource validation
def create_user_validator():
    """Create user validation dependency."""
    async def validate_user_exists(
        user_id: UUID = Path(..., description="User ID"),
        db: AsyncSession = Depends(get_db)
    ):
        from app.models.user import User
        return await validate_resource_exists(
            user_id, User, db, "User not found"
        )
    return validate_user_exists


def create_unit_validator():
    """Create unit validation dependency."""
    async def validate_unit_exists(
        unit_id: UUID = Path(..., description="Unit ID"),
        db: AsyncSession = Depends(get_db)
    ):
        from app.models.unit import Unit
        return await validate_resource_exists(
            unit_id, Unit, db, "Unit not found"
        )
    return validate_unit_exists


def create_product_validator():
    """Create product validation dependency."""
    async def validate_product_exists(
        product_id: UUID = Path(..., description="Product ID"),
        db: AsyncSession = Depends(get_db)
    ):
        from app.models.product import Product
        return await validate_resource_exists(
            product_id, Product, db, "Product not found"
        )
    return validate_product_exists


def create_supplier_validator():
    """Create supplier validation dependency."""
    async def validate_supplier_exists(
        supplier_id: UUID = Path(..., description="Supplier ID"),
        db: AsyncSession = Depends(get_db)
    ):
        from app.models.supplier import Supplier
        return await validate_resource_exists(
            supplier_id, Supplier, db, "Supplier not found"
        )
    return validate_supplier_exists

# =====================================================
# BUSINESS LOGIC DEPENDENCIES
# =====================================================

async def get_stock_alert_filter(
    alert_type: Optional[str] = Query(
        None, 
        regex="^(low|reorder|expired|all)$",
        description="Stock alert type: low, reorder, expired, or all"
    )
) -> Optional[str]:
    """
    Get stock alert filter parameter.
    
    Args:
        alert_type: Type of stock alerts to filter
    
    Returns:
        Optional[str]: Alert type filter
    
    Usage:
        @app.get("/stock/alerts")
        async def get_stock_alerts(
            alert_filter: Optional[str] = Depends(get_stock_alert_filter)
        ):
            # Filter stock alerts by type
    """
    return alert_type


def get_approval_required_filter(
    requires_approval: Optional[bool] = Query(None, description="Filter by approval requirement")
) -> Optional[bool]:
    """
    Get approval requirement filter.
    
    Args:
        requires_approval: Whether to filter by approval requirement
    
    Returns:
        Optional[bool]: Approval filter value
    """
    return requires_approval


# =====================================================
# REQUEST CONTEXT DEPENDENCIES
# =====================================================

def get_request_context(request: Request) -> Dict[str, Any]:
    """
    Extract useful context from the request.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Dict[str, Any]: Request context information
    
    Usage:
        @app.post("/orders/")
        async def create_order(
            context: Dict[str, Any] = Depends(get_request_context)
        ):
            # Use context for audit logging
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "timestamp": datetime.utcnow(),
        "path": request.url.path,
        "query_params": dict(request.query_params)
    }

# =====================================================
# RESPONSE FORMATTING DEPENDENCIES
# =====================================================

class SuccessResponse(BaseModel):
    """
    Standard success response model.
    """
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime = datetime.utcnow()


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


def create_success_response(
    message: str, 
    data: Any = None
) -> SuccessResponse:
    """
    Create standardized success response.
    
    Args:
        message: Success message
        data: Response data
    
    Returns:
        SuccessResponse: Formatted success response
    """
    return SuccessResponse(message=message, data=data)


def create_error_response(
    error: str, 
    detail: Optional[str] = None
) -> ErrorResponse:
    """
    Create standardized error response.
    
    Args:
        error: Error message
        detail: Additional error details
    
    Returns:
        ErrorResponse: Formatted error response
    """
    return ErrorResponse(error=error, detail=detail)

# =====================================================
# COMBINED COMMON DEPENDENCIES
# =====================================================

class CommonQueryParams(BaseModel):
    """
    Combined common query parameters.
    """
    pagination: PaginationParams
    sort: SortParams
    search: Optional[str] = None
    date_range: Tuple[Optional[date], Optional[date]]
    status: Optional[str] = None


async def get_common_params(
    pagination: PaginationParams = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    search: Optional[str] = Depends(get_search_filter),
    date_range: Tuple[Optional[date], Optional[date]] = Depends(get_date_range_filter),
    status: Optional[str] = Depends(get_status_filter)
) -> CommonQueryParams:
    """
    Get all common query parameters in one dependency.
    
    Args:
        pagination: Pagination parameters
        sort: Sort parameters
        search: Search filter
        date_range: Date range filter
        status: Status filter
    
    Returns:
        CommonQueryParams: All common parameters
    
    Usage:
        @app.get("/products/")
        async def get_products(params: CommonQueryParams = Depends(get_common_params)):
            # Access params.pagination, params.sort, etc.
    """
    return CommonQueryParams(
        pagination=pagination,
        sort=sort,
        search=search,
        date_range=date_range,
        status=status
    )

# =====================================================
# AUDIT LOGGING DEPENDENCY
# =====================================================

async def log_api_access(
    current_user = Depends(get_current_user),
    request_context: Dict[str, Any] = Depends(get_request_context)
):
    """
    Log API access for audit purposes.
    
    Args:
        current_user: Current authenticated user
        request_context: Request context information
    
    Note:
        This is a dependency that logs but doesn't return anything.
        Use it to automatically log API access.
    
    Usage:
        @app.get("/sensitive-endpoint")
        async def sensitive_operation(
            _audit: None = Depends(log_api_access)  # Underscore to show it's not used
        ):
            # API access will be logged automatically
    """
    logger.info(
        f"API Access: {current_user.email} ({current_user.role}) "
        f"accessed {request_context['method']} {request_context['path']} "
        f"from {request_context['client_ip']}"
    )

# =====================================================
# EXPORT COMMONLY USED ITEMS
# =====================================================

# Create validator instances for common resources
ValidateUser = create_user_validator()
ValidateUnit = create_unit_validator()
ValidateProduct = create_product_validator()
ValidateSupplier = create_supplier_validator()

# Export all commonly used dependencies
__all__ = [
    # Database and auth (re-exports)
    "GetDB",
    "GetCurrentUser", 
    "GetCurrentUserId",
    "GetUserAccessibleUnits",
    "GetCurrentActiveUser",
    "GetCurrentActiveSuperuser", 
    "get_current_active_superuser",
    "CheckUnitAccess",
    
    # Pagination
    "PaginationParams",
    "PaginatedResponse",
    "get_pagination_params",
    
    # Sorting and filtering
    "SortParams",
    "get_sort_params",
    "get_date_range_filter",
    "get_search_filter",
    "get_status_filter",
    
    # Multi-tenant
    "get_accessible_unit_filter",
    "validate_unit_access",
    
    # Validation
    "validate_uuid_path",
    "ValidateUser",
    "ValidateUnit", 
    "ValidateProduct",
    "ValidateSupplier",
    
    # Business logic
    "get_stock_alert_filter",
    "get_approval_required_filter",
    
    # Context and responses
    "get_request_context",
    "SuccessResponse",
    "ErrorResponse",
    "create_success_response",
    "create_error_response",
    
    # Combined params
    "CommonQueryParams",
    "get_common_params",
    
    # Audit
    "log_api_access"
]