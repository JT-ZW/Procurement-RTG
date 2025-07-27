#!/usr/bin/env python3
"""
Quick database check script
"""
import os
import psycopg2
from sqlalchemy import create_engine, text

def check_database():
    """Check database state"""
    try:
        # Use DATABASE_URL environment variable or default
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password123@localhost:5432/procurement_db')
        
        # Create sync engine directly
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row.table_name for row in result]
            print("📋 Available tables:")
            for table in tables:
                print(f"  • {table}")
            
            # Check if products table has data
            result = conn.execute(text("SELECT COUNT(*) as count FROM products"))
            products_count = result.first().count
            print(f"\n📦 Products in database: {products_count}")
            
            # Check if e_catalogue_view exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count FROM information_schema.views 
                WHERE table_schema = 'public' AND table_name = 'e_catalogue_view'
            """))
            view_exists = result.first().count > 0
            print(f"👁️ e_catalogue_view exists: {view_exists}")
            
            if view_exists:
                try:
                    result = conn.execute(text("SELECT COUNT(*) as count FROM e_catalogue_view"))
                    view_count = result.first().count
                    print(f"📊 Records in e_catalogue_view: {view_count}")
                except Exception as e:
                    print(f"❌ Error querying e_catalogue_view: {e}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()
