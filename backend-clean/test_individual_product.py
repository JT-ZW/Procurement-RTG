#!/usr/bin/env python3
"""
Test the specific product endpoint that's failing
"""
import asyncio
import httpx

async def test_specific_product():
    """Test individual product endpoint"""
    print("🔐 Authenticating...")
    
    # Login first
    login_data = {
        "username": "admin@hotel.com",
        "password": "password123"
    }
    
    async with httpx.AsyncClient() as client:
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
        
        # First get a product ID from the products list
        print("📦 Getting products list to find a valid ID...")
        response = await client.get(
            "http://localhost:8001/api/v1/products/",
            headers=headers
        )
        
        if response.status_code == 200:
            products = response.json()
            if products:
                product_id = products[0]["id"]
                product_name = products[0]["name"]
                print(f"✅ Found product ID: {product_id} ({product_name})")
                
                # Now test the individual product endpoint
                print(f"🔍 Testing individual product endpoint...")
                response = await client.get(
                    f"http://localhost:8001/api/v1/products/{product_id}",
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    product = response.json()
                    print(f"✅ Individual product retrieved: {product['name']}")
                    print(f"   ID: {product['id']}")
                    print(f"   Stock: {product['current_stock_quantity']}")
                    print(f"   Status: {product['stock_status']}")
                else:
                    print(f"❌ Error: {response.text}")
            else:
                print("❌ No products found")
        else:
            print(f"❌ Failed to get products list: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_specific_product())
