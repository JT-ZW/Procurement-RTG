#!/usr/bin/env python3
"""
Script to create test users directly in the database.
This bypasses the API authentication requirements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SyncSessionLocal
from app.crud import crud_user
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.models.user import User
import uuid

def create_test_users_db():
    """Create test users directly in the database"""
    
    db: Session = SyncSessionLocal()
    
    try:
        print("🏨 Creating test users for Hotel Procurement System...")
        print("=" * 50)
        
        # Test user data
        test_users = [
            {
                "email": "admin@hotel.com",
                "password": "admin123",
                "full_name": "Hotel Admin",
                "role": "procurement_admin",
                "is_active": True
            },
            {
                "email": "user@hotel.com", 
                "password": "user123",
                "full_name": "Hotel User",
                "role": "unit_manager",
                "is_active": True
            }
        ]
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = crud_user.get_by_email(db, email=user_data["email"])
            if existing_user:
                print(f"⚠️  User {user_data['email']} already exists, skipping...")
                continue
            
            # Create user schema
            user_create = UserCreate(
                email=user_data["email"],
                password=user_data["password"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=user_data["is_active"]
            )
            
            # Create user
            try:
                user = crud_user.create(db, obj_in=user_create)
                print(f"✅ Created user: {user_data['email']} (ID: {user.id})")
            except Exception as e:
                print(f"❌ Failed to create {user_data['email']}: {str(e)}")
        
        print("\n" + "=" * 50)
        print("Test users creation completed!")
        print("\n📋 Login credentials:")
        print("Admin: admin@hotel.com / admin123")
        print("User:  user@hotel.com / user123")
        print("\n🌐 You can now test login at: http://localhost:5173")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users_db()
