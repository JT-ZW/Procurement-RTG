#!/usr/bin/env python3
"""
Simple test to check server health
"""
import requests
import json

def test_server_health():
    """Test if server is responding"""
    print("🔐 Testing server health...")
    
    # Login first
    login_data = {
        "username": "admin@hotel.com",
        "password": "password123"
    }
    
    try:
        # Authenticate
        print("Authenticating...")
        response = requests.post(
            "http://localhost:8001/api/v1/auth/login",
            data=login_data,
            timeout=10
        )
        
        print(f"Auth Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.text}")
            return
        
        token_data = response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Authentication successful!")
        
        # Test main products endpoint
        print("Testing products endpoint...")
        response = requests.get(
            "http://localhost:8001/api/v1/products/?limit=2",
            headers=headers,
            timeout=10
        )
        
        print(f"Products Status: {response.status_code}")
        
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Found {len(products)} products")
            if products:
                print(f"   Sample: {products[0]['name']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_server_health()
