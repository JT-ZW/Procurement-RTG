#!/usr/bin/env python3
"""
Database initialization script for the Procurement System.
Creates tables and initial data including superuser.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User
from app.models.unit import Unit
from uuid import uuid4

async def init_database():
    """Initialize database with tables and basic data."""
    
    # Create async engine
    async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(async_url, echo=True)
    
    async with engine.begin() as conn:
        # Create all tables
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")
    
    # Create session for data insertion
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if superuser already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == "admin@hotel.com")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("✅ Superuser admin@hotel.com already exists")
            else:
                # Create superuser
                print("Creating superuser...")
                superuser = User(
                    id=uuid4(),
                    email="admin@hotel.com",
                    first_name="Hotel",
                    last_name="Admin",
                    hashed_password=get_password_hash("admin123"),
                    role="superuser",
                    is_active=True,
                    is_superuser=True
                )
                session.add(superuser)
                print("✅ Superuser created!")
            
            # Create a regular test user
            result = await session.execute(
                select(User).where(User.email == "user@hotel.com")
            )
            existing_test_user = result.scalar_one_or_none()
            
            if not existing_test_user:
                print("Creating test user...")
                test_user = User(
                    id=uuid4(),
                    email="user@hotel.com",
                    first_name="Test",
                    last_name="User", 
                    hashed_password=get_password_hash("user123"),
                    role="unit_manager",
                    is_active=True,
                    is_superuser=False
                )
                session.add(test_user)
                print("✅ Test user created!")
            
            await session.commit()
            
            print("\n" + "="*50)
            print("🎉 Database initialization completed successfully!")
            print("="*50)
            print("📋 Login Credentials:")
            print("   Superuser: admin@hotel.com / admin123")
            print("   Test User: user@hotel.com / user123")
            print("="*50)
            
        except Exception as e:
            print(f"❌ Error during data insertion: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    print("🏨 Initializing Hotel Procurement System Database...")
    print("="*50)
    try:
        asyncio.run(init_database())
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
