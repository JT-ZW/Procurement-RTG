#!/usr/bin/env python3
"""
Check existing tables in Supabase database
"""
import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_existing_tables():
    """Check what tables already exist in the database"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            print("🔍 Checking existing tables in your Supabase database...\n")
            
            # Get all tables in public schema
            result = connection.execute(text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            
            if tables:
                print("📋 Existing tables found:")
                print("-" * 50)
                for table in tables:
                    print(f"  • {table[0]} ({table[1]})")
                
                print(f"\n📊 Total tables: {len(tables)}")
                
                # Check if any of our expected tables exist
                our_tables = [
                    'users', 'units', 'suppliers', 'product_categories', 'products',
                    'purchase_requisitions', 'purchase_requisition_items', 
                    'purchase_orders', 'purchase_order_items', 'invoices', 
                    'invoice_items', 'budget_approvals', 'notifications'
                ]
                
                existing_our_tables = [table[0] for table in tables if table[0] in our_tables]
                
                if existing_our_tables:
                    print(f"\n⚠️  Found {len(existing_our_tables)} of our expected tables:")
                    for table in existing_our_tables:
                        print(f"    • {table}")
                
                # Check for any data in key tables
                print("\n🔍 Checking for existing data...")
                for table in existing_our_tables[:5]:  # Check first 5 tables
                    try:
                        count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        print(f"    • {table}: {count} records")
                    except Exception as e:
                        print(f"    • {table}: Error checking - {str(e)[:50]}")
                        
            else:
                print("✅ No tables found in public schema - database is clean!")
                
            print("\n" + "="*60)
            print("RECOMMENDATIONS:")
            print("="*60)
            
            if tables:
                if existing_our_tables:
                    print("🔄 Option 1: DROP existing tables and recreate (DESTRUCTIVE)")
                    print("🔧 Option 2: Modify schema to work with existing tables")
                    print("📝 Option 3: Use different table names/schema")
                else:
                    print("✅ You can proceed with setup - no conflicts expected")
            else:
                print("✅ Database is clean - proceed with full setup")
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_existing_tables()
