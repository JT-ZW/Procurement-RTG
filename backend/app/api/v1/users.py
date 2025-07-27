from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.crud import crud_user, crud_unit
from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserListResponse,
    UserProfileUpdate,
    UserRoleUpdate,
    UserStatusUpdate,
    UserSearchParams,
    UserStatsResponse,
    UserActivityResponse
)
from app.schemas.auth import PasswordChange
from app.utils.multi_tenant import (
    check_unit_access, 
    get_user_units, 
    is_unit_manager,
    can_manage_user
)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
def read_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    unit_id: Optional[UUID] = Query(None, description="Filter by unit ID"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and email"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
) -> Any:
    """
    Retrieve users with filtering and pagination.
    Access control: 
    - Superusers see all users
    - Procurement admins see all users
    - Unit managers see users in their units
    - Store managers/staff see users in their units
    """
    # Determine user access scope
    if current_user.is_superuser or current_user.role == "procurement_admin":
        # Can see all users
        accessible_unit_ids = None
    else:
        # Can only see users in their assigned units
        accessible_unit_ids = get_user_units(db, user_id=current_user.id)
        if not accessible_unit_ids:
            return {"items": [], "total": 0}
        
        # If specific unit requested, verify access
        if unit_id:
            if unit_id not in accessible_unit_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to view users in this unit"
                )
            accessible_unit_ids = [unit_id]
    
    users, total = crud_user.get_multi_with_filters(
        db,
        unit_ids=accessible_unit_ids,
        role=role,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return {"items": users, "total": total}


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new user.
    Access control:
    - Superusers can create any user
    - Procurement admins can create unit-level users
    - Unit managers can create staff for their units
    """
    # Check if user has permission to create users
    if not current_user.is_superuser:
        if current_user.role not in ["procurement_admin", "unit_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create users"
            )
        
        # Unit managers can only create staff roles
        if current_user.role == "unit_manager":
            allowed_roles = ["store_manager", "store_staff"]
            if user_in.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Unit managers can only create users with roles: {', '.join(allowed_roles)}"
                )
    
    # Check if email already exists
    existing_user = crud_user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Verify unit assignments if provided
    if user_in.unit_assignments:
        for assignment in user_in.unit_assignments:
            # Check if unit exists
            unit = crud_unit.get(db, id=assignment.unit_id)
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit {assignment.unit_id} not found"
                )
            
            # Check if current user can assign to this unit
            if not current_user.is_superuser and current_user.role != "procurement_admin":
                check_unit_access(db, user=current_user, unit_id=assignment.unit_id)
    
    user = crud_user.create(db, obj_in=user_in, created_by=current_user.id)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get user by ID.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if current user can view this user
    if not can_manage_user(db, manager=current_user, target_user=user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update user.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not can_manage_user(db, manager=current_user, target_user=user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )
    
    # Prevent users from updating their own role or status (except superusers)
    if user_id == current_user.id and not current_user.is_superuser:
        if user_in.role is not None or user_in.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users cannot update their own role or status"
            )
    
    # Role change restrictions
    if user_in.role and user_in.role != user.role:
        if not current_user.is_superuser:
            if current_user.role == "unit_manager":
                allowed_roles = ["store_manager", "store_staff"]
                if user_in.role not in allowed_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Unit managers can only assign roles: {', '.join(allowed_roles)}"
                    )
    
    # Hash password if provided
    if user_in.password:
        user_in.password = security.get_password_hash(user_in.password)
    
    user = crud_user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete user (soft delete).
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not can_manage_user(db, manager=current_user, target_user=user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this user"
        )
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot delete themselves"
        )
    
    # Check if user is the last manager of any unit
    if user.role in ["unit_manager", "store_manager"]:
        managed_units = get_user_units(db, user_id=user_id)
        for unit_id in managed_units:
            if is_unit_manager(db, user=user, unit_id=unit_id):
                managers_count = crud_unit.count_unit_managers(db, unit_id=unit_id)
                if managers_count <= 1:
                    unit = crud_unit.get(db, id=unit_id)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot delete the last manager of unit: {unit.name if unit else unit_id}"
                    )
    
    crud_user.remove(db, id=user_id)
    return {"message": "User deleted successfully"}


# User Profile Management
@router.put("/{user_id}/profile", response_model=UserResponse)
def update_user_profile(
    user_id: UUID,
    profile_in: UserProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update user profile information.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can update their own profile, or managers can update their subordinates
    if user_id != current_user.id:
        if not can_manage_user(db, manager=current_user, target_user=user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this user's profile"
            )
    
    user = crud_user.update_profile(db, db_obj=user, obj_in=profile_in)
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update user role.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not can_manage_user(db, manager=current_user, target_user=user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user's role"
        )
    
    # Prevent self role change for non-superusers
    if user_id == current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot change their own role"
        )
    
    # Role assignment restrictions
    if not current_user.is_superuser:
        if current_user.role == "unit_manager":
            allowed_roles = ["store_manager", "store_staff"]
            if role_update.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Unit managers can only assign roles: {', '.join(allowed_roles)}"
                )
    
    user = crud_user.update_role(db, db_obj=user, new_role=role_update.role)
    return user


@router.put("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: UUID,
    status_update: UserStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Activate or deactivate user.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not can_manage_user(db, manager=current_user, target_user=user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user's status"
        )
    
    # Prevent self-deactivation
    if user_id == current_user.id and not status_update.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot deactivate themselves"
        )
    
    user = crud_user.update_status(db, db_obj=user, is_active=status_update.is_active)
    return user


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: UUID,
    temporary_password: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Reset user password (admin function).
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only superusers and procurement admins can reset passwords
    if not current_user.is_superuser and current_user.role != "procurement_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to reset passwords"
        )
    
    hashed_password = security.get_password_hash(temporary_password)
    crud_user.update_password(db, user_id=user_id, hashed_password=hashed_password)
    
    # TODO: Send email with temporary password
    # send_password_reset_email(user.email, temporary_password)
    
    return {"message": "Password reset successfully. User will receive email with temporary password."}


# User Search and Filtering
@router.get("/search", response_model=UserListResponse)
def search_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    q: str = Query(..., min_length=2, description="Search query"),
    unit_id: Optional[UUID] = Query(None, description="Filter by unit"),
    role: Optional[str] = Query(None, description="Filter by role"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
) -> Any:
    """
    Search users by name, email, or other criteria.
    """
    # Determine accessible units
    if current_user.is_superuser or current_user.role == "procurement_admin":
        accessible_unit_ids = None
    else:
        accessible_unit_ids = get_user_units(db, user_id=current_user.id)
        if unit_id and unit_id not in accessible_unit_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to search users in this unit"
            )
    
    users, total = crud_user.search_users(
        db,
        search_query=q,
        unit_ids=accessible_unit_ids if not unit_id else [unit_id],
        role=role,
        limit=limit
    )
    
    return {"items": users, "total": total}


# User Statistics and Activity
@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def read_user_stats(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    period: str = Query("month", regex="^(week|month|quarter|year)$")
) -> Any:
    """
    Get user activity statistics.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can see their own stats, managers can see their subordinates' stats
    if user_id != current_user.id:
        if not can_manage_user(db, manager=current_user, target_user=user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this user's statistics"
            )
    
    stats = crud_user.get_user_statistics(db, user_id=user_id, period=period)
    return stats


@router.get("/{user_id}/activity", response_model=List[UserActivityResponse])
def read_user_activity(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    limit: int = Query(50, ge=1, le=200, description="Number of activities to return")
) -> Any:
    """
    Get user recent activity log.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can see their own activity, managers can see their subordinates' activity
    if user_id != current_user.id:
        if not can_manage_user(db, manager=current_user, target_user=user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this user's activity"
            )
    
    activities = crud_user.get_user_activities(db, user_id=user_id, limit=limit)
    return activities


# Bulk User Operations
@router.post("/bulk-create", response_model=List[UserResponse])
def bulk_create_users(
    users_in: List[UserCreate],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create multiple users in bulk.
    """
    # Only superusers and procurement admins can bulk create
    if not current_user.is_superuser and current_user.role != "procurement_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for bulk user creation"
        )
    
    if len(users_in) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create more than 50 users at once"
        )
    
    # Validate all users before creating any
    emails = [user.email for user in users_in]
    if len(emails) != len(set(emails)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate emails found in bulk creation request"
        )
    
    # Check for existing emails
    for email in emails:
        if crud_user.get_by_email(db, email=email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {email} already exists"
            )
    
    created_users = []
    for user_in in users_in:
        try:
            user = crud_user.create(db, obj_in=user_in, created_by=current_user.id)
            created_users.append(user)
        except Exception as e:
            # Rollback and raise error
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating user {user_in.email}: {str(e)}"
            )
    
    return created_users


@router.get("/roles/available")
def get_available_roles(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get roles that current user can assign to others.
    """
    if current_user.is_superuser:
        roles = [
            "superuser", "procurement_admin", "unit_manager", 
            "store_manager", "store_staff", "supplier_user"
        ]
    elif current_user.role == "procurement_admin":
        roles = ["unit_manager", "store_manager", "store_staff"]
    elif current_user.role == "unit_manager":
        roles = ["store_manager", "store_staff"]
    else:
        roles = []
    
    return {
        "available_roles": roles,
        "descriptions": {
            "superuser": "Full system access",
            "procurement_admin": "Group-level procurement management",
            "unit_manager": "Hotel unit management",
            "store_manager": "Store operations management",
            "store_staff": "Basic store operations",
            "supplier_user": "External supplier access"
        }
    }