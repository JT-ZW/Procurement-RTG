#!/usr/bin/env python3
"""
Simple server connectivity test
"""
import requests
import time

def test_server_connection():
    """Test if the backend server is running"""
    print("🔍 Testing server connectivity...")
    
    ports_to_try = [8000, 8001]
    
    for port in ports_to_try:
        url = f"http://localhost:{port}"
        print(f"\n🔌 Trying port {port}...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server is running on port {port}!")
                print(f"   Health response: {response.json()}")
                
                # Test root endpoint
                root_response = requests.get(f"{url}/", timeout=5)
                if root_response.status_code == 200:
                    print(f"✅ Root endpoint working: {root_response.json()}")
                
                return port
            else:
                print(f"❌ Health check failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ No server running on port {port}")
        except requests.exceptions.Timeout:
            print(f"❌ Server on port {port} is not responding")
        except Exception as e:
            print(f"❌ Error testing port {port}: {str(e)}")
    
    print("\n🚫 No backend server found!")
    print("💡 Please start your backend server with: python main.py")
    return None

if __name__ == "__main__":
    test_server_connection()
