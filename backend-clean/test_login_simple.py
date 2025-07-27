#!/usr/bin/env python3
"""
Simple login test
"""
import requests
import json

def test_login():
    """Test login functionality"""
    print("🔑 Testing login...")
    
    # Test data
    login_data = {
        "email": "admin@hotel.com",
        "password": "password123"
    }
    
    try:
        # Test the login endpoint
        print("📡 Sending login request...")
        response = requests.post(
            "http://localhost:8001/auth/login/json", 
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📋 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ LOGIN SUCCESSFUL!")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
            print(f"   Role: {data.get('user', {}).get('role', 'N/A')}")
            print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
            
            # Test the /me endpoint
            headers = {"Authorization": f"Bearer {data.get('access_token')}"}
            me_response = requests.get("http://localhost:8001/auth/me", headers=headers)
            
            if me_response.status_code == 200:
                print("✅ Token validation successful!")
                return True
            else:
                print(f"⚠️  Token validation failed: {me_response.status_code}")
                
        else:
            print(f"❌ LOGIN FAILED")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API")
        print("   Make sure your backend is running: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return False

if __name__ == "__main__":
    print("🧪 AUTHENTICATION TEST")
    print("=" * 30)
    test_login()
