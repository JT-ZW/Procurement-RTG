"""
User CRUD Operations
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser:
    async def get(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            user_uuid = UUID(user_id)
            result = await db.execute(select(User).where(User.id == user_uuid))
            return result.scalar_one_or_none()
        except ValueError:
            return None

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get multiple users."""
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """Create new user."""
        # Check if user already exists
        existing_user = await self.get_by_email(db, email=obj_in.email)
        if existing_user:
            raise ValueError(f"User with email {obj_in.email} already exists")

        # Create user data
        create_data = obj_in.dict()
        password = create_data.pop("password")
        create_data["hashed_password"] = get_password_hash(password)

        # Create user
        db_obj = User(**create_data)
        db.add(db_obj)
        
        try:
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await db.rollback()
            raise ValueError(f"User with email {obj_in.email} already exists")

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        """Update user."""
        update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
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


# Create instance
user = CRUDUser()
