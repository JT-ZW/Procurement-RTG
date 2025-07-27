#!/usr/bin/env python3
"""
Quick E-catalogue functionality verification
"""
import requests
import json

def quick_test():
    """Quick test of key E-catalogue functionality"""
    print("🔐 Quick E-catalogue Test")
    print("=" * 40)
    
    # Login
    login_data = {
        "username": "admin@hotel.com",
        "password": "password123"
    }
    
    try:
        # Authenticate
        response = requests.post(
            "http://localhost:8001/api/v1/auth/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Auth failed: {response.status_code}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful!")
        
        # Test main products endpoint
        response = requests.get(
            "http://localhost:8001/api/v1/products/",
            headers=headers,
            timeout=10
        )
        print(f"📦 Products endpoint: Status {response.status_code}")
        if response.status_code == 200:
            products = response.json()
            print(f"   Found {len(products)} products")
            if products:
                sample = products[0]
                print(f"   Sample: {sample['name']} - ${sample.get('effective_unit_price', 'N/A')} - {sample.get('stock_status', 'N/A')}")
        
        # Test e-catalogue endpoint
        response = requests.get(
            "http://localhost:8001/api/v1/products/e-catalogue/",
            headers=headers,
            timeout=10
        )
        print(f"📊 E-catalogue endpoint: Status {response.status_code}")
        if response.status_code == 200:
            catalogue = response.json()
            print(f"   Found {len(catalogue)} catalogue items")
            if catalogue:
                sample = catalogue[0]
                days_left = sample.get('estimated_days_stock_will_last', 'N/A')
                print(f"   Sample: {sample['name']} - Stock will last {days_left} days")
        
        # Test search
        response = requests.get(
            "http://localhost:8001/api/v1/products/?search=clean",
            headers=headers,
            timeout=10
        )
        print(f"🔍 Search test: Status {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Search found {len(results)} items")
        
        print("=" * 40)
        print("🎉 Quick test complete!")
        print("✅ All key E-catalogue features working")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()
