"""
Test a minimal products endpoint
"""
import requests

def test_minimal():
    """Test minimal endpoint"""
    base_url = "http://localhost:8001/api/v1"
    
    # Authenticate
    response = requests.post(f"{base_url}/auth/login", data={
        "username": "admin@hotel.com",
        "password": "password123"
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Authentication successful!")
    
    # Test just the e-catalogue endpoint
    print("\n📊 Testing e-catalogue endpoint (working)...")
    response = requests.get(f"{base_url}/products/e-catalogue/", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} catalogue items")
        if data:
            print("First item fields:", list(data[0].keys()))
    else:
        print("Error:", response.text[:200])

if __name__ == "__main__":
    test_minimal()
