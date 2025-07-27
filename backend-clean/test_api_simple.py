#!/usr/bin/env python3
"""
Quick API test script
"""
import requests
import json

def test_api():
    """Test API endpoints to identify the issue"""
    base_url = "http://localhost:8001/api/v1"
    
    # Authenticate
    print("🔐 Authenticating...")
    response = requests.post(f"{base_url}/auth/login", data={
        "username": "admin@hotel.com",
        "password": "password123"
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(response.text)
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Authentication successful!")
    
    # Test products endpoint
    print("\n📦 Testing products endpoint...")
    response = requests.get(f"{base_url}/products/", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print("Response text:", response.text[:500])
    else:
        data = response.json()
        print(f"Found {len(data)} products")
    
    # Test e-catalogue endpoint
    print("\n📊 Testing e-catalogue endpoint...")
    response = requests.get(f"{base_url}/products/e-catalogue/", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print("Response text:", response.text[:500])
    else:
        data = response.json()
        print(f"Found {len(data)} catalogue items")

if __name__ == "__main__":
    test_api()
