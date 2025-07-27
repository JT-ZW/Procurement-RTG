#!/usr/bin/env python3
"""
Database initialization script
Creates tables and sample data
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.database import Base, get_async_database_url
from app.models.user import User
from app.models.unit import Unit
from app.models.product import Product
from app.core.security import get_password_hash
from app.core.database import AsyncSessionLocal
from uuid import uuid4

async def init_database():
    """Initialize database with tables and sample data."""
    print(f"🏨 Initializing {settings.APP_NAME} Database...")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(get_async_database_url(), echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created!")
    
    # Create sample data
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == "admin@hotel.com")
            )
            
            if not result.scalar_one_or_none():
                # Create admin user
                admin_user = User(
                    id=uuid4(),
                    email="admin@hotel.com",
                    hashed_password=get_password_hash("admin123"),
                    first_name="System",
                    last_name="Administrator",
                    role="superuser",
                    is_active=True,
                    is_superuser=True
                )
                session.add(admin_user)
                print("✅ Admin user created: admin@hotel.com / admin123")
            
            # Create test user
            result = await session.execute(
                select(User).where(User.email == "user@hotel.com")
            )
            
            if not result.scalar_one_or_none():
                test_user = User(
                    id=uuid4(),
                    email="user@hotel.com",
                    hashed_password=get_password_hash("user123"),
                    first_name="Test",
                    last_name="User",
                    role="staff",
                    is_active=True,
                    is_superuser=False
                )
                session.add(test_user)
                print("✅ Test user created: user@hotel.com / user123")
            
            # Create sample units
            result = await session.execute(select(Unit))
            if not result.scalars().all():
                for i in range(1, 9):
                    unit = Unit(
                        id=uuid4(),
                        name=f"Hotel Unit {i}",
                        code=f"HOTEL{i:03d}",
                        description=f"Hotel property unit {i}",
                        address=f"123 Hotel Street {i}",
                        city="Hotel City",
                        country="Country",
                        is_active=True
                    )
                    session.add(unit)
                print("✅ Sample hotel units created (HOTEL001-HOTEL008)")
            
            await session.commit()
            
            print("\n" + "=" * 50)
            print("🎉 Database initialization completed!")
            print("=" * 50)
            print("📋 Login Credentials:")
            print("   Admin: admin@hotel.com / admin123")
            print("   User:  user@hotel.com / user123")
            print("=" * 50)
            print(f"🚀 Start the server: uvicorn main:app --reload")
            print(f"📖 API Docs: http://localhost:8001/docs")
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(init_database())
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
