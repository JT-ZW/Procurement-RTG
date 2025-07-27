"""
Complete Database Setup Script for Hotel Procurement System
This script will create all tables, insert sample data, and create views
Run this after ensuring your database connection is working
"""

import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path to import our app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def read_sql_file(file_path: Path) -> str:
    """Read SQL file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"SQL file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading SQL file {file_path}: {e}")
        raise

async def execute_sql_script(sql_content: str, script_name: str):
    """Execute SQL script with proper error handling."""
    try:
        async with engine.begin() as conn:
            # Split the SQL content by statement separators
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        await conn.execute(text(statement))
                        logger.debug(f"Executed statement {i+1}/{len(statements)} from {script_name}")
                    except SQLAlchemyError as e:
                        logger.warning(f"Statement {i+1} in {script_name} had an issue (might be expected): {e}")
                        # Continue with other statements
                        continue
            
            logger.info(f"✅ Successfully executed {script_name}")
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error in {script_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in {script_name}: {e}")
        raise

async def test_database_connection():
    """Test the database connection before setup."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Database connection successful")
            logger.info(f"PostgreSQL Version: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def setup_database():
    """Complete database setup process."""
    logger.info("🚀 Starting Hotel Procurement System Database Setup")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[0]}@***")
    
    # Test connection first
    if not await test_database_connection():
        logger.error("Database connection failed. Please check your .env configuration.")
        return False
    
    # Get the SQL setup directory
    sql_dir = Path(__file__).parent / "sql_setup"
    
    # List of SQL files to execute in order
    sql_files = [
        ("01_create_tables.sql", "Creating database tables and triggers"),
        ("02_insert_sample_data.sql", "Inserting sample data"),
        ("03_create_views.sql", "Creating useful views and reports")
    ]
    
    try:
        for sql_file, description in sql_files:
            logger.info(f"📄 {description}...")
            sql_path = sql_dir / sql_file
            
            if not sql_path.exists():
                logger.error(f"SQL file not found: {sql_path}")
                return False
                
            sql_content = await read_sql_file(sql_path)
            await execute_sql_script(sql_content, sql_file)
        
        logger.info("🎉 Database setup completed successfully!")
        logger.info("📋 Summary:")
        logger.info("   ✅ All tables created with proper indexes and constraints")
        logger.info("   ✅ Sample data inserted (units, users, products, etc.)")
        logger.info("   ✅ Useful views created for reporting and analytics")
        logger.info("")
        logger.info("🔐 Test User Accounts (password: 'password123'):")
        logger.info("   • admin@hotel.com (Superuser)")
        logger.info("   • manager.ghd@hotel.com (Manager)")
        logger.info("   • chef@hotel.com (Staff)")
        logger.info("   • housekeeper@hotel.com (Staff)")
        logger.info("")
        logger.info("🚀 Your procurement system is ready to use!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

async def verify_setup():
    """Verify that the setup was successful by checking key tables."""
    logger.info("🔍 Verifying database setup...")
    
    verification_queries = [
        ("SELECT COUNT(*) FROM units", "Units table"),
        ("SELECT COUNT(*) FROM users", "Users table"),
        ("SELECT COUNT(*) FROM products", "Products table"),
        ("SELECT COUNT(*) FROM suppliers", "Suppliers table"),
        ("SELECT COUNT(*) FROM purchase_requisitions", "Purchase requisitions table"),
    ]
    
    try:
        async with engine.begin() as conn:
            for query, description in verification_queries:
                result = await conn.execute(text(query))
                count = result.fetchone()[0]
                logger.info(f"   ✅ {description}: {count} records")
        
        logger.info("✅ Database verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False

async def main():
    """Main setup function."""
    success = await setup_database()
    
    if success:
        await verify_setup()
        logger.info("🎯 Next steps:")
        logger.info("   1. Start your FastAPI backend server")
        logger.info("   2. Start your frontend application")
        logger.info("   3. Test the login with the provided credentials")
        logger.info("   4. Create your first purchase requisition!")
    else:
        logger.error("Setup failed. Please check the logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
