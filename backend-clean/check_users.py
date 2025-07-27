#!/usr/bin/env python3
"""
Quick script to check existing users in the database
"""
from app.core.database import engine
from sqlalchemy import text

def check_users():
    """Check what users exist in the database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT email, role, is_active FROM users WHERE is_active = true'))
            users = result.fetchall()
            print('Available users:')
            if users:
                for user in users:
                    print(f'  Email: {user.email}, Role: {user.role}, Active: {user.is_active}')
            else:
                print('  No active users found')
            
            # Also check if there are inactive users
            result = conn.execute(text('SELECT COUNT(*) as total FROM users'))
            total = result.first()
            print(f'\nTotal users in database: {total.total}')
            
    except Exception as e:
        print(f'Error checking users: {e}')

if __name__ == "__main__":
    check_users()
