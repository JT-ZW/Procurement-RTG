#!/usr/bin/env python3
"""
Test the dashboard stats endpoint
"""
import requests

BASE_URL = "http://localhost:8001"

def test_dashboard_stats():
    print("🧪 TESTING DASHBOARD STATS ENDPOINT")
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
            print(f"✅ Login successful")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test dashboard stats endpoint
    print("\n🔍 Testing /admin/dashboard-stats endpoint...")
    try:
        stats_response = requests.get(f"{BASE_URL}/api/v1/admin/dashboard-stats", headers=headers)
        print(f"Status: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ Dashboard stats loaded successfully:")
            print(f"   • Total Products: {stats.get('total_products', 0)}")
            print(f"   • Total Suppliers: {stats.get('total_suppliers', 0)}")
            print(f"   • Total Units: {stats.get('total_units', 0)}")
            print(f"   • Total Users: {stats.get('total_users', 0)}")
            print(f"   • Total Requisitions: {stats.get('total_requisitions', 0)}")
            print(f"   • Urgent Count: {stats.get('urgent_count', 0)}")
            print(f"   • Pending Approval: {stats.get('pending_approval', 0)}")
            if stats.get('status_counts'):
                print(f"   • Status Breakdown:")
                for status, count in stats['status_counts'].items():
                    print(f"     - {status}: {count}")
        else:
            print(f"❌ Error: {stats_response.text}")
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    test_dashboard_stats()
