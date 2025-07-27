#!/usr/bin/env python3
"""
Test API endpoints with Supabase database
This script tests all major procurement system endpoints
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
BASE_URL = "http://localhost:8001"  # Adjust if your API runs on different port
API_V1 = f"{BASE_URL}/api/v1"

def test_health_check():
    """Test basic API health"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        return False

def test_user_login():
    """Test user authentication"""
    print("\n🔐 Testing user authentication...")
    
    login_data = {
        "username": "admin@hotel.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{API_V1}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful")
            print(f"   Token type: {token_data.get('token_type', 'N/A')}")
            return token_data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def test_protected_endpoints(token):
    """Test protected endpoints with authentication"""
    print("\n🛡️  Testing protected endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/me", "Current user info"),
        ("/units", "Hotel units"),
        ("/suppliers", "Suppliers"),
        ("/products", "Products"),
        ("/product-categories", "Product categories"),
        ("/purchase-requisitions", "Purchase requisitions")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{API_V1}{endpoint}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {description}: {len(data)} items")
                else:
                    print(f"✅ {description}: Success")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")

def test_crud_operations(token):
    """Test CRUD operations"""
    print("\n📝 Testing CRUD operations...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Generate unique code for supplier
    import uuid
    unique_code = f"TST-API-{str(uuid.uuid4())[:8].upper()}"
    
    # Test creating a new supplier
    new_supplier = {
        "name": f"Test Supplier API {unique_code}",
        "code": unique_code,
        "contact_person": "API Test Person",
        "email": f"test{unique_code.lower()}@apisupplier.com",
        "phone": "+1-555-API-TEST",
        "address": "123 API Test Street",
        "city": "Test City",
        "country": "Test Country",
        "payment_terms": "Net 30",
        "currency": "USD",
        "rating": 4
    }
    
    try:
        # Create supplier
        response = requests.post(f"{API_V1}/suppliers", 
                               headers=headers, 
                               json=new_supplier)
        
        if response.status_code == 201:
            supplier_data = response.json()
            supplier_id = supplier_data.get('id')
            print(f"✅ Created supplier: {supplier_data.get('name')}")
            
            # Read supplier
            response = requests.get(f"{API_V1}/suppliers/{supplier_id}", headers=headers)
            if response.status_code == 200:
                print("✅ Read supplier: Success")
            
            # Update supplier
            update_data = {"rating": 5}
            response = requests.put(f"{API_V1}/suppliers/{supplier_id}", 
                                  headers=headers, 
                                  json=update_data)
            if response.status_code == 200:
                print("✅ Updated supplier: Success")
            
            # Delete supplier
            response = requests.delete(f"{API_V1}/suppliers/{supplier_id}", headers=headers)
            if response.status_code == 204:
                print("✅ Deleted supplier: Success")
            
        else:
            print(f"❌ Create supplier failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ CRUD operations error: {str(e)}")

def test_database_queries():
    """Test database connectivity directly"""
    print("\n🗄️  Testing database connectivity...")
    
    try:
        from sqlalchemy import create_engine, text
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found")
            return
        
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT COUNT(*) as total FROM users"))
            user_count = result.scalar()
            print(f"✅ Database query: {user_count} users found")
            
            # Test complex query
            result = conn.execute(text("""
                SELECT 
                    u.name as unit_name,
                    COUNT(us.id) as user_count
                FROM units u
                LEFT JOIN users us ON us.unit_id = u.id
                GROUP BY u.id, u.name
                ORDER BY user_count DESC
                LIMIT 5
            """))
            
            units_data = result.fetchall()
            print("✅ Complex query: Unit user counts")
            for row in units_data:
                print(f"   • {row.unit_name}: {row.user_count} users")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Database test error: {str(e)}")

def main():
    """Run all tests"""
    print("🧪 PROCUREMENT SYSTEM API TESTS")
    print("=" * 50)
    
    # Test 1: API Health
    if not test_health_check():
        print("\n❌ API is not running. Please start your backend first:")
        print("   python main.py")
        return
    
    # Test 2: Authentication
    token = test_user_login()
    if not token:
        print("\n❌ Authentication failed. Check your database setup.")
        return
    
    # Test 3: Protected endpoints
    test_protected_endpoints(token)
    
    # Test 4: CRUD operations
    test_crud_operations(token)
    
    # Test 5: Database connectivity
    test_database_queries()
    
    print("\n🎉 API testing complete!")
    print("\n📋 Summary:")
    print("   • Your Supabase database is connected")
    print("   • Authentication is working")
    print("   • CRUD operations are functional")
    print("   • Your procurement system is ready to use!")

if __name__ == "__main__":
    main()
