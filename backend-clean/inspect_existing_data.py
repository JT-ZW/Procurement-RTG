#!/usr/bin/env python3
"""
Script to inspect existing data in Supabase database
"""
import os
import asyncio
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    exit(1)

def inspect_existing_data():
    """Inspect existing data in the database"""
    print("🔍 Inspecting existing data in your Supabase database...\n")
    
    # Create synchronous engine for inspection
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Get all tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print("📋 Detailed table inspection:")
            print("=" * 60)
            
            for table in tables:
                print(f"\n🏷️  Table: {table}")
                
                # Get column info
                columns = inspector.get_columns(table)
                print("   Columns:")
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"     • {col['name']}: {col['type']} {nullable}{default}")
                
                # Get sample data
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   📊 Records: {count}")
                    
                    if count > 0 and count <= 10:
                        # Show sample data for small tables
                        result = conn.execute(text(f"SELECT * FROM {table} LIMIT 5"))
                        rows = result.fetchall()
                        if rows:
                            print("   📝 Sample data (first 5 rows):")
                            for i, row in enumerate(rows, 1):
                                print(f"     {i}. {dict(row._mapping)}")
                    elif count > 10:
                        # Show just a few sample records for larger tables
                        result = conn.execute(text(f"SELECT * FROM {table} LIMIT 2"))
                        rows = result.fetchall()
                        if rows:
                            print("   📝 Sample data (first 2 rows):")
                            for i, row in enumerate(rows, 1):
                                print(f"     {i}. {dict(row._mapping)}")
                                
                except Exception as e:
                    print(f"   ⚠️  Could not read data: {str(e)}")
                
                print("-" * 40)
            
            print(f"\n📊 Summary: Found {len(tables)} tables")
            
    except Exception as e:
        print(f"❌ Error inspecting database: {str(e)}")
        return False
    
    finally:
        engine.dispose()
    
    return True

def provide_recommendations():
    """Provide recommendations based on existing data"""
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS:")
    print("=" * 60)
    
    print("""
🔄 OPTION 1: Clean Slate (Recommended for development)
   • Drop all existing tables
   • Create fresh schema with our procurement system
   • Best for testing and development
   
🔧 OPTION 2: Merge with Existing Data
   • Keep existing data
   • Add missing tables/columns
   • More complex but preserves data
   
📝 OPTION 3: Separate Schema
   • Create procurement schema
   • Keep existing data in public schema
   • Clean separation of concerns
   
🚀 OPTION 4: Database Migration
   • Create migration scripts
   • Gradually move to new structure
   • Professional approach
""")

if __name__ == "__main__":
    if inspect_existing_data():
        provide_recommendations()
