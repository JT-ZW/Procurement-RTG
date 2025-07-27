"""
Test Database Connection to Supabase
"""
import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal
from app.core.config import settings

async def test_connection():
    """Test the database connection."""
    try:
        print(f"Testing connection to: {settings.DATABASE_URL[:50]}...")
        
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ PostgreSQL Version: {version}")
            
        # Test session creation
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT current_database(), current_user"))
            db_name, user = result.fetchone()
            print(f"✓ Connected to database: {db_name}")
            print(f"✓ Connected as user: {user}")
            
        # Test table creation capability
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS connection_test (
                    id SERIAL PRIMARY KEY,
                    test_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await conn.execute(text("""
                INSERT INTO connection_test (test_message) 
                VALUES ('Connection test successful')
            """))
            
            result = await conn.execute(text("""
                SELECT test_message, created_at 
                FROM connection_test 
                ORDER BY created_at DESC 
                LIMIT 1
            """))
            
            message, created = result.fetchone()
            print(f"✓ Table operations work: {message} at {created}")
            
            # Clean up test table
            await conn.execute(text("DROP TABLE IF EXISTS connection_test"))
            print("✓ Cleanup completed")
            
        print("\n🎉 Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
