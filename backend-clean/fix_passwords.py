#!/usr/bin/env python3
"""
Simple password fix for authentication
"""
import os
import sys
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

# Create password context
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def fix_passwords():
    """Fix user passwords in database"""
    print("🔧 Fixing user passwords...")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Generate new hash for password123
            new_hash = pwd_context.hash('password123')
            print(f"📝 New password hash: {new_hash[:50]}...")
            
            # Update all users
            result = conn.execute(
                text("UPDATE users SET hashed_password = :hash"), 
                {"hash": new_hash}
            )
            conn.commit()
            
            rows_updated = result.rowcount
            print(f"✅ Updated {rows_updated} users")
            
            # Show updated users
            result = conn.execute(text("SELECT email, role FROM users"))
            users = result.fetchall()
            
            print("\n👥 Updated users:")
            for user in users:
                print(f"   • {user.email} ({user.role}) - password: password123")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    fix_passwords()
