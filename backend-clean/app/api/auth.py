"""
Authentication API Routes
"""
from datetime import timedelta
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    get_current_active_superuser
)
from app.crud.user import user as crud_user
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse, UserLogin

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    user = await crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Mock units for now - will be implemented properly later
    units = [
        {"id": "hotel-1", "name": "Hotel Unit 1", "code": "HOTEL001"}
    ]
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user),
        units=units
    )


@router.post("/login/json", response_model=Token)
async def login_json(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """JSON login endpoint for frontend applications."""
    user = await crud_user.authenticate(
        db, email=user_in.email, password=user_in.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Mock units for now
    units = [
        {"id": "hotel-1", "name": "Hotel Unit 1", "code": "HOTEL001"}
    ]
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user),
        units=units
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new user - open registration."""
    try:
        user = await crud_user.create(db, obj_in=user_in)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user profile."""
    return UserResponse.from_orm(current_user)


@router.post("/test-token", response_model=UserResponse)
async def test_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Test access token."""
    return UserResponse.from_orm(current_user)
