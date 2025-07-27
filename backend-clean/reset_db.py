#!/usr/bin/env python3
"""
Database reset and clean initialization
This will drop existing tables and create new ones with our clean schema
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base, get_async_database_url, AsyncSessionLocal
from app.models.user import User
from app.models.unit import Unit
from app.models.product import Product
from app.core.security import get_password_hash
from uuid import uuid4

async def reset_and_init_database():
    """Reset database and create clean schema."""
    print(f"🏨 Resetting and Initializing {settings.APP_NAME} Database...")
    print("⚠️  WARNING: This will DROP all existing tables!")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(get_async_database_url(), echo=True)
    
    async with engine.begin() as conn:
        print("🗑️  Dropping existing tables...")
        
        # Drop all tables (be careful - this removes all data!)
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        
        print("✅ Existing tables dropped!")
        
        print("🔨 Creating new tables with clean schema...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ New database tables created!")
    
    # Create sample data
    async with AsyncSessionLocal() as session:
        try:
            print("👤 Creating users...")
            
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
            
            print("🏨 Creating hotel units...")
            
            # Create sample units
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
            print("🎉 Database reset and initialization completed!")
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
    # Ask for confirmation
    confirm = input("⚠️  This will DELETE ALL existing data. Continue? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Database reset cancelled.")
        sys.exit(0)
    
    try:
        asyncio.run(reset_and_init_database())
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        sys.exit(1)
