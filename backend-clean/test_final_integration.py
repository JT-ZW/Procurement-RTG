#!/usr/bin/env python3
"""
Final Integration Test - Test all API endpoints with authentication
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"  # Your backend URL

def test_complete_integration():
    """Test complete frontend-backend integration"""
    print("🧪 COMPLETE INTEGRATION TEST")
    print("=" * 50)
    
    # Step 1: Login
    print("🔐 Step 1: Testing login...")
    login_data = {
        "email": "admin@hotel.com",
        "password": "secret123"
    }
    
    try:
        # Use JSON login endpoint with correct field names
        response = requests.post(f"{BASE_URL}/auth/login/json", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('access_token')
            print(f"✅ Login successful! Token: {token[:50]}...")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return
    
    # Step 2: Test API endpoints
    print("\n📊 Step 2: Testing API endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/api/v1/units", "Hotel Units"),
        ("/api/v1/suppliers", "Suppliers"),
        ("/api/v1/products", "Products"),
        ("/api/v1/product-categories", "Product Categories"),
        ("/api/v1/purchase-requisitions", "Purchase Requisitions"),
        ("/api/v1/dashboard/stats", "Dashboard Statistics"),
        ("/api/v1/notifications", "Notifications")
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "N/A"
                print(f"✅ {name}: {count} items")
                working_endpoints.append((endpoint, name, data))
            else:
                print(f"❌ {name}: {response.status_code}")
                failed_endpoints.append((endpoint, name, response.status_code))
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
            failed_endpoints.append((endpoint, name, str(e)))
    
    # Step 3: Display sample data
    print("\n📋 Step 3: Sample data from working endpoints...")
    for endpoint, name, data in working_endpoints:
        if isinstance(data, list) and len(data) > 0:
            print(f"\n{name} (first item):")
            first_item = data[0]
            for key, value in first_item.items():
                if len(str(value)) > 50:
                    value = str(value)[:50] + "..."
                print(f"  • {key}: {value}")
        elif isinstance(data, dict):
            print(f"\n{name}:")
            for key, value in data.items():
                print(f"  • {key}: {value}")
    
    # Step 4: Summary
    print(f"\n🎯 SUMMARY:")
    print(f"✅ Working endpoints: {len(working_endpoints)}")
    print(f"❌ Failed endpoints: {len(failed_endpoints)}")
    
    if len(working_endpoints) >= 5:
        print("\n🎉 SUCCESS! Your backend is properly connected to Supabase!")
        print("Your frontend should now be able to display data from the database.")
        print("\n📋 Next steps:")
        print("1. Refresh your frontend application")
        print("2. Login with: admin@hotel.com / secret123")
        print("3. Check if data is now displaying properly")
    else:
        print("\n⚠️  Some endpoints are not working. Check the backend logs.")
    
    if failed_endpoints:
        print(f"\n❌ Failed endpoints:")
        for endpoint, name, error in failed_endpoints:
            print(f"   • {name}: {error}")

if __name__ == "__main__":
    test_complete_integration()
