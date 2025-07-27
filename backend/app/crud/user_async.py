from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, func, text, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserUpdate,
    UserProfileUpdate,
    UserStatsResponse,
    UserActivityResponse
)


class CRUDUser:
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """Get user by username (if username field exists)."""
        if hasattr(User, 'username'):
            result = await db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        return None

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser

    async def get(self, db: AsyncSession, id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create new user."""
        # Hash password if provided
        create_data = obj_in.dict()
        if "password" in create_data:
            create_data["hashed_password"] = get_password_hash(create_data.pop("password"))
        
        # Set defaults
        create_data.setdefault("is_active", True)
        create_data.setdefault("is_superuser", False)
        create_data.setdefault("role", "store_staff")
        
        db_obj = User(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: User, 
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update user."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        # Hash password if being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get multiple users."""
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def remove(self, db: AsyncSession, *, id: UUID) -> User:
        """Remove user (soft delete)."""
        obj = await self.get(db, id=id)
        if obj:
            obj.is_deleted = True
            obj.deleted_at = datetime.utcnow()
            await db.commit()
            await db.refresh(obj)
        return obj


# Create instance
crud_user = CRUDUser()
