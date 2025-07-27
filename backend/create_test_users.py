#!/usr/bin/env python3
"""
Script to create test users for the procurement system.
Run this after the backend server is started.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def create_test_users():
    """Create test users for login testing"""
    
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
    
    print("🏨 Creating test users for Hotel Procurement System...")
    print("=" * 50)
    
    for user_data in test_users:
        try:
            # Try to create user via API
            response = requests.post(
                f"{BASE_URL}/api/v1/users/",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                print(f"✅ Created user: {user_data['email']}")
            elif response.status_code == 422:
                # Try to get more details about validation error
                error_detail = response.json()
                print(f"❌ Validation error for {user_data['email']}: {error_detail}")
            else:
                print(f"❌ Failed to create {user_data['email']}: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to backend server. Make sure it's running on http://127.0.0.1:8000")
            break
        except Exception as e:
            print(f"❌ Error creating user {user_data['email']}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Test users creation completed!")
    print("\n📋 Login credentials:")
    print("Admin: admin@hotel.com / admin123")
    print("User:  user@hotel.com / user123")

if __name__ == "__main__":
    create_test_users()
