#!/usr/bin/env python3
"""
Check actual database connection
"""
import asyncio
from app.core.database import get_db, AsyncSessionLocal
from sqlalchemy import text

async def check_db_connection():
    """Check what database we're actually connected to"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT current_database(), version()"))
            row = result.first()
            print(f"Connected to database: {row[0]}")
            print(f"Database version: {row[1]}")
            
            # Check if e_catalogue_view exists
            result = await session.execute(text("""
                SELECT COUNT(*) as count FROM information_schema.views 
                WHERE table_schema = 'public' AND table_name = 'e_catalogue_view'
            """))
            view_exists = result.first().count > 0
            print(f"e_catalogue_view exists: {view_exists}")
            
            if view_exists:
                result = await session.execute(text("SELECT COUNT(*) FROM e_catalogue_view"))
                view_count = result.first().count
                print(f"Records in e_catalogue_view: {view_count}")
                
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db_connection())
