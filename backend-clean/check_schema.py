#!/usr/bin/env python3
"""
Check existing database schema
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_async_database_url, AsyncSessionLocal

async def check_database_schema():
    """Check existing database schema."""
    print("🔍 Checking existing database schema...")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(get_async_database_url(), echo=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check users table columns
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            if columns:
                print("📋 Existing 'users' table columns:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            else:
                print("❌ No 'users' table found")
            
            print("\n" + "=" * 50)
            
            # Check what tables exist
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            print("📋 Existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
                
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_database_schema())
