"""
User Management API Routes
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import AsyncSessionWrapper

from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_superuser
from app.crud.user import user as crud_user
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: AsyncSessionWrapper = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """Get users (admin only)."""
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    return [UserResponse.from_orm(user) for user in users]


@router.post("/", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """Create new user (admin only)."""
    try:
        user = await crud_user.create(db, obj_in=user_in)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user by ID."""
    user = await crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can only see their own profile unless they're superuser
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return UserResponse.from_orm(user)
