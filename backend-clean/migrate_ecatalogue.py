#!/usr/bin/env python3
"""
Database Migration Script for E-catalogue Module 1
This script applies the necessary database changes for enhanced product management
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to sys.path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


async def run_migration():
    """Apply database migration for E-catalogue enhancement"""
    print("🚀 Starting E-catalogue Database Migration")
    print("=" * 50)
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        print("📝 Reading migration SQL...")
        migration_file = "sql_setup/04_update_products_for_ecatalogue.sql"
        
        if not os.path.exists(migration_file):
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔄 Applying migration...")
        with engine.connect() as connection:
            # Split the SQL into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"   Executing statement {i}/{len(statements)}...")
                    try:
                        connection.execute(text(statement))
                        connection.commit()
                    except SQLAlchemyError as e:
                        # Some statements might fail if already applied (like ALTER TABLE ADD COLUMN IF NOT EXISTS)
                        # This is expected behavior for idempotent migrations
                        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                            print(f"   ⚠️  Statement {i} already applied (skipped)")
                            continue
                        else:
                            raise e
        
        print("✅ Migration completed successfully!")
        print("\n📊 Migration Summary:")
        print("   • Added contract_price column")
        print("   • Added current_stock_quantity column") 
        print("   • Added estimated_consumption_rate_per_day column")
        print("   • Added supplier_id relationship")
        print("   • Added unit_id relationship")
        print("   • Added specifications JSONB column")
        print("   • Added tracking timestamps")
        print("   • Created e_catalogue_view with calculations")
        print("   • Added performance indexes")
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        with engine.connect() as connection:
            # Check if new columns exist
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name IN ('contract_price', 'current_stock_quantity', 'estimated_consumption_rate_per_day')
            """))
            
            columns = [row[0] for row in result]
            if len(columns) >= 3:
                print("✅ New columns verified successfully")
            else:
                print(f"⚠️  Only {len(columns)} new columns found")
            
            # Check if view exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_name = 'e_catalogue_view'
                )
            """))
            
            view_exists = result.scalar()
            if view_exists:
                print("✅ E-catalogue view created successfully")
            else:
                print("❌ E-catalogue view creation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    result = asyncio.run(run_migration())
    sys.exit(0 if result else 1)
