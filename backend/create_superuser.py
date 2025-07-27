#!/usr/bin/env python3
"""
Script to create a superuser directly in the database.
This bypasses API authentication requirements.
"""

import sys
import asyncio
from sqlalchemy.orm import Session
from app.core.database import SyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from uuid import uuid4

def create_superuser():
    """Create a superuser for testing"""
    
    db = SyncSessionLocal()
    
    try:
        # Check if superuser already exists
        existing_user = db.query(User).filter(User.email == "admin@hotel.com").first()
        if existing_user:
            print("✅ Superuser admin@hotel.com already exists")
            print("📋 You can login with: admin@hotel.com / admin123")
            return
        
        # Create superuser
        hashed_password = get_password_hash("admin123")
        
        superuser = User(
            id=uuid4(),
            email="admin@hotel.com",
            first_name="Hotel",
            last_name="Admin",
            hashed_password=hashed_password,
            role="superuser",
            is_active=True,
            is_superuser=True
        )
        
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
        
        print("✅ Superuser created successfully!")
        print("📋 Login credentials:")
        print("   Email: admin@hotel.com")
        print("   Password: admin123")
        print("   Role: superuser")
        
        # Also create a regular user
        regular_user = User(
            id=uuid4(),
            email="user@hotel.com",
            first_name="Hotel",
            last_name="User",
            hashed_password=get_password_hash("user123"),
            role="unit_manager",
            is_active=True,
            is_superuser=False
        )
        
        db.add(regular_user)
        db.commit()
        db.refresh(regular_user)
        
        print("✅ Regular user also created!")
        print("📋 Additional login credentials:")
        print("   Email: user@hotel.com")
        print("   Password: user123")
        print("   Role: unit_manager")
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🏨 Creating superuser for Hotel Procurement System...")
    print("=" * 50)
    create_superuser()
    print("=" * 50)
    print("🎉 You can now test the login at your frontend URL!")
