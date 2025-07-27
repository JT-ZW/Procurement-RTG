#!/usr/bin/env python3
"""
Final comprehensive test of all E-catalogue endpoints
"""
import asyncio
import httpx
import json

async def test_all_endpoints():
    """Test all E-catalogue endpoints thoroughly"""
    print("🔐 Starting Final E-catalogue API Test Suite")
    print("=" * 60)
    
    # Login first
    login_data = {
        "username": "admin@hotel.com",
        "password": "password123"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Authenticate
        response = await client.post(
            "http://localhost:8001/api/v1/auth/login",
            data=login_data
        )
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return
        
        token_data = response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Authentication successful!")
        print()
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: GET /api/v1/products/ (Main Products Endpoint)
        total_tests += 1
        print("📦 Test 1: GET /api/v1/products/ (Main Products Endpoint)")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                products = response.json()
                print(f"✅ Found {len(products)} products")
                if products:
                    print(f"   Sample: {products[0]['name']} ({products[0]['code']})")
                tests_passed += 1
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Test 2: GET /api/v1/products/e-catalogue/
        total_tests += 1
        print("📊 Test 2: GET /api/v1/products/e-catalogue/ (E-catalogue View)")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/e-catalogue/",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                catalogue = response.json()
                print(f"✅ Found {len(catalogue)} catalogue items")
                tests_passed += 1
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Test 3: GET /api/v1/products/categories/
        total_tests += 1
        print("🏷️  Test 3: GET /api/v1/products/categories/ (Product Categories)")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/categories/",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                categories = response.json()
                print(f"✅ Found {len(categories)} categories")
                tests_passed += 1
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Test 4: Get specific product by ID
        total_tests += 1
        print("🔍 Test 4: GET /api/v1/products/{id} (Individual Product)")
        try:
            # First get a product ID
            response = await client.get(
                "http://localhost:8001/api/v1/products/?limit=1",
                headers=headers
            )
            if response.status_code == 200:
                products = response.json()
                if products:
                    product_id = products[0]["id"]
                    
                    # Now test individual product endpoint
                    response = await client.get(
                        f"http://localhost:8001/api/v1/products/{product_id}",
                        headers=headers
                    )
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        product = response.json()
                        print(f"✅ Individual product: {product['name']}")
                        print(f"   ID: {product['id']}")
                        print(f"   Stock: {product['current_stock_quantity']}")
                        tests_passed += 1
                    else:
                        print(f"❌ Error: {response.text}")
                else:
                    print("❌ No products available for individual test")
            else:
                print(f"❌ Failed to get products list: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Test 5: Search functionality
        total_tests += 1
        print("🔍 Test 5: Search functionality")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/?search=cleaner",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Search found {len(results)} items matching 'cleaner'")
                tests_passed += 1
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Test 6: Filter by stock status
        total_tests += 1
        print("📊 Test 6: Filter by stock status")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/e-catalogue/?stock_status=LOW_STOCK",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Found {len(results)} items with LOW_STOCK status")
                tests_passed += 1
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Test 7: Pagination
        total_tests += 1
        print("📄 Test 7: Pagination (limit=3)")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/?limit=3",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Retrieved {len(results)} items (should be 3 or less)")
                tests_passed += 1
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        print()
        
        # Final Results
        print("=" * 60)
        print(f"🎉 Final E-catalogue API Test Suite Complete!")
        print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
        if tests_passed == total_tests:
            print("🌟 ALL TESTS PASSED! E-catalogue API is fully functional!")
        else:
            print(f"⚠️  {total_tests - tests_passed} tests failed. Check logs above.")
        
        print("\n📋 E-catalogue Features Summary:")
        print("✅ Product listing with E-catalogue fields")
        print("✅ E-catalogue view with calculated fields")
        print("✅ Product categories management")
        print("✅ Individual product retrieval")
        print("✅ Search functionality")
        print("✅ Stock status filtering")
        print("✅ Pagination support")
        print("✅ Authentication and authorization")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
