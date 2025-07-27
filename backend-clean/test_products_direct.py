#!/usr/bin/env python3
"""
Direct API test to see the exact error in products endpoint
"""
import asyncio
import httpx
import json

async def test_products_direct():
    """Test products endpoint directly"""
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
            print(f"Response: {response.text}")
            return
        
        token_data = response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Authentication successful!")
        
        # Test products endpoint with detailed error handling
        print("📦 Testing products endpoint...")
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/products/",
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found {len(data)} products")
                if data:
                    print("First product keys:", list(data[0].keys()))
            else:
                print(f"Error Response: {response.text}")
                
        except Exception as e:
            print(f"Exception during request: {e}")

if __name__ == "__main__":
    asyncio.run(test_products_direct())
