#!/usr/bin/env python3
"""
Test the specific endpoints that are failing
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_endpoints():
    print("🧪 TESTING SPECIFIC ENDPOINTS")
    print("=" * 50)
    
    # First, log in to get a token
    print("🔐 Getting authentication token...")
    login_data = {
        "username": "admin@hotel.com",
        "password": "password123"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get("access_token")
            print(f"✅ Login successful, token type: {token_data.get('token_type')}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /me endpoint
    print("\n🔍 Testing /me endpoint...")
    try:
        me_response = requests.get(f"{BASE_URL}/api/v1/me", headers=headers)
        print(f"Status: {me_response.status_code}")
        if me_response.status_code == 200:
            print(f"✅ User info: {me_response.json()}")
        else:
            print(f"❌ Error: {me_response.text}")
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    # Test purchase-requisitions endpoint
    print("\n🔍 Testing /purchase-requisitions endpoint...")
    try:
        req_response = requests.get(f"{BASE_URL}/api/v1/purchase-requisitions", headers=headers)
        print(f"Status: {req_response.status_code}")
        if req_response.status_code == 200:
            data = req_response.json()
            print(f"✅ Purchase requisitions: {len(data)} items")
        else:
            print(f"❌ Error: {req_response.text}")
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    # Test supplier creation
    print("\n🔍 Testing supplier creation...")
    import uuid
    unique_code = f"DEBUG-{str(uuid.uuid4())[:8].upper()}"
    supplier_data = {
        "name": f"Debug Test Supplier {unique_code}",
        "code": unique_code,
        "contact_person": "Debug Person",
        "email": f"debug{unique_code.lower()}@test.com",
        "phone": "+1-555-DEBUG",
        "address": "123 Debug Street",
        "city": "Debug City",
        "country": "Debug Country"
    }
    
    try:
        create_response = requests.post(f"{BASE_URL}/api/v1/suppliers", 
                                      json=supplier_data, headers=headers)
        print(f"Status: {create_response.status_code}")
        if create_response.status_code in [200, 201]:
            print(f"✅ Supplier created: {create_response.json()}")
        else:
            print(f"❌ Error: {create_response.text}")
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    test_endpoints()
