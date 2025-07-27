#!/usr/bin/env python3
"""
Test authentication and fix password issues
"""
import os
import asyncio
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def test_and_fix_passwords():
    """Test current passwords and fix them if needed"""
    print("🔐 Testing and fixing authentication...")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check current users
            result = conn.execute(text("SELECT email, hashed_password FROM users LIMIT 3"))
            users = result.fetchall()
            
            if not users:
                print("❌ No users found in database")
                return False
            
            print(f"📋 Found {len(users)} users")
            
            # Test passwords
            test_passwords = ['password123', 'secret123']
            working_password = None
            
            for user in users:
                email = user.email
                stored_hash = user.hashed_password
                
                print(f"\n👤 Testing user: {email}")
                print(f"   Hash: {stored_hash[:50]}...")
                
                for test_pwd in test_passwords:
                    try:
                        if pwd_context.verify(test_pwd, stored_hash):
                            print(f"   ✅ Password '{test_pwd}' works!")
                            working_password = test_pwd
                            break
                        else:
                            print(f"   ❌ Password '{test_pwd}' doesn't work")
                    except Exception as e:
                        print(f"   ⚠️  Error testing '{test_pwd}': {str(e)}")
                
                if working_password:
                    break
            
            if not working_password:
                print("\n🔧 No passwords work, creating new hashes...")
                
                # Update all users with 'password123'
                new_hash = pwd_context.hash('password123')
                conn.execute(text("UPDATE users SET hashed_password = :hash"), 
                           {"hash": new_hash})
                conn.commit()
                
                print("✅ Updated all users to use 'password123'")
                working_password = 'password123'
            
            print(f"\n🎉 Authentication setup complete!")
            print(f"   Working password: {working_password}")
            print(f"   Test users:")
            
            # Show test users
            result = conn.execute(text("SELECT email, first_name, last_name, role FROM users"))
            users = result.fetchall()
            
            for user in users:
                print(f"   • {user.email} ({user.first_name} {user.last_name}) - {user.role}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        engine.dispose()

def test_api_endpoint():
    """Test if the API endpoints are accessible"""
    print("\n🌐 Testing API endpoints...")
    
    try:
        import requests
        
        # Test health endpoint
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and accessible")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - make sure it's running on port 8001")
        return False
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        return False

def test_login():
    """Test login with the working password"""
    print("\n🔑 Testing login...")
    
    try:
        import requests
        
        login_data = {
            "email": "admin@hotel.com",
            "password": "password123"
        }
        
        response = requests.post("http://localhost:8001/auth/login/json", 
                               json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
            print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🏨 PROCUREMENT SYSTEM - AUTHENTICATION TEST")
    print("=" * 50)
    
    # Step 1: Fix passwords
    if test_and_fix_passwords():
        print("\n" + "=" * 50)
        
        # Step 2: Test API
        if test_api_endpoint():
            # Step 3: Test login
            test_login()
        else:
            print("\n💡 To start the API, run: python main.py")
    
    print("\n🏁 Test complete!")
