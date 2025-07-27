#!/usr/bin/env python3
"""
Test API endpoints to verify data is being returned correctly
"""
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8001"  # Your backend URL (updated to correct port)
API_V1 = f"{BASE_URL}/api/v1"

def test_login_and_get_token():
    """Login and get authentication token"""
    print("🔐 Testing login...")
    
    # Try both login endpoints
    login_endpoints = [
        f"{BASE_URL}/auth/login/json",
        f"{API_V1}/auth/login", 
        f"{BASE_URL}/auth/login"
    ]
    
    login_data = {
        "email": "admin@hotel.com",
        "password": "secret123"
    }
    
    for endpoint in login_endpoints:
        try:
            print(f"   Trying: {endpoint}")
            response = requests.post(endpoint, json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                print(f"✅ Login successful at {endpoint}")
                print(f"   Token: {token_data.get('access_token', 'N/A')[:50]}...")
                return token_data.get('access_token'), endpoint
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    return None, None

def test_api_endpoints(token):
    """Test various API endpoints that the frontend might use"""
    print("\n🔍 Testing API endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different endpoint patterns
    endpoints_to_test = [
        # User endpoints
        ("/auth/me", "Current user"),
        ("/api/v1/auth/me", "Current user (v1)"),
        ("/me", "User profile"),
        
        # Data endpoints
        ("/api/v1/units", "Hotel units"),
        ("/units", "Hotel units (direct)"),
        ("/api/v1/suppliers", "Suppliers"),
        ("/suppliers", "Suppliers (direct)"),
        ("/api/v1/products", "Products"),
        ("/products", "Products (direct)"),
        ("/api/v1/requisitions", "Purchase requisitions"),
        ("/requisitions", "Requisitions (direct)"),
        ("/api/v1/purchase-requisitions", "Purchase requisitions (alt)"),
        
        # Dashboard data
        ("/api/v1/dashboard", "Dashboard data"),
        ("/dashboard", "Dashboard (direct)"),
        ("/api/v1/stats", "Statistics"),
    ]
    
    working_endpoints = []
    
    for endpoint, description in endpoints_to_test:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {description}: {len(data)} items")
                    if len(data) > 0:
                        print(f"   Sample: {json.dumps(data[0], indent=2)[:200]}...")
                else:
                    print(f"✅ {description}: {type(data)} - {str(data)[:100]}...")
                working_endpoints.append((endpoint, description, data))
            elif response.status_code == 404:
                print(f"❌ {description}: Endpoint not found")
            else:
                print(f"⚠️  {description}: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
    
    return working_endpoints

def test_frontend_api_calls():
    """Test the specific API calls your frontend is likely making"""
    print("\n🖥️  Testing Frontend API Patterns...")
    
    # Common frontend API patterns
    frontend_patterns = [
        "GET /api/v1/auth/me",
        "GET /api/v1/units",
        "GET /api/v1/suppliers", 
        "GET /api/v1/products",
        "GET /api/v1/purchase-requisitions",
        "GET /api/v1/dashboard/stats",
    ]
    
    token, login_endpoint = test_login_and_get_token()
    if not token:
        print("❌ Cannot test frontend patterns - login failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for pattern in frontend_patterns:
        method, endpoint = pattern.split(" ", 1)
        url = f"{BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "1 object"
                print(f"✅ {pattern}: {count}")
            else:
                print(f"❌ {pattern}: {response.status_code}")
        except Exception as e:
            print(f"❌ {pattern}: {str(e)}")

def check_cors_headers():
    """Check if CORS is properly configured"""
    print("\n🌐 Testing CORS Configuration...")
    
    try:
        # Test preflight request
        response = requests.options(f"{BASE_URL}/api/v1/units", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        })
        
        print(f"Preflight response: {response.status_code}")
        print("CORS Headers:", dict(response.headers))
        
    except Exception as e:
        print(f"CORS test error: {str(e)}")

def main():
    """Run all tests"""
    print("🧪 FRONTEND-BACKEND INTEGRATION TEST")
    print("=" * 50)
    
    # Test 1: Login
    token, login_endpoint = test_login_and_get_token()
    if not token:
        print("\n❌ Login failed - cannot proceed with other tests")
        return
    
    # Test 2: API endpoints
    working_endpoints = test_api_endpoints(token)
    
    # Test 3: Frontend patterns
    test_frontend_api_calls()
    
    # Test 4: CORS
    check_cors_headers()
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"✅ Login working: {login_endpoint}")
    print(f"✅ Working endpoints: {len(working_endpoints)}")
    
    if working_endpoints:
        print("\n📋 Data available:")
        for endpoint, desc, data in working_endpoints:
            if isinstance(data, list) and len(data) > 0:
                print(f"   • {desc}: {len(data)} items")
    
    print(f"\n💡 NEXT STEPS:")
    print("1. Check browser console for frontend JavaScript errors")
    print("2. Verify frontend is calling the correct API endpoints")
    print("3. Check if frontend authentication token is being sent")
    print("4. Verify frontend is parsing the API responses correctly")

if __name__ == "__main__":
    main()
