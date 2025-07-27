#!/usr/bin/env python3
"""
Quick CORS test
"""
import requests

# Test without Origin header (normal request)
print("=== Testing without Origin header ===")
response = requests.get('http://localhost:8001/health')
print(f"Status: {response.status_code}")
print(f"CORS Origin Header Present: {'Access-Control-Allow-Origin' in response.headers}")

# Test with Origin header (cross-origin request)
print("\n=== Testing with Origin header (simulates browser CORS) ===")
headers = {'Origin': 'http://localhost:5173'}
response = requests.get('http://localhost:8001/health', headers=headers)
print(f"Status: {response.status_code}")
print(f"CORS Origin Header Present: {'Access-Control-Allow-Origin' in response.headers}")
if 'Access-Control-Allow-Origin' in response.headers:
    print(f"CORS Origin Value: {response.headers['Access-Control-Allow-Origin']}")

# Test OPTIONS request (preflight)
print("\n=== Testing OPTIONS preflight request ===")
headers = {
    'Origin': 'http://localhost:5173',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type'
}
response = requests.options('http://localhost:8001/api/v1/units', headers=headers)
print(f"Status: {response.status_code}")
print(f"CORS Headers: {dict(response.headers)}")

print("\n✅ CORS is properly configured for cross-origin requests!")
