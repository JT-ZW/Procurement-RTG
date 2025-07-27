#!/usr/bin/env python3
"""
Check available database tables
"""
from app.core.database import sync_engine
from sqlalchemy import text

def check_tables():
    """Check what tables exist in the database"""
    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row.table_name for row in result]
            print('📋 Available tables:')
            for table in tables:
                print(f'  • {table}')
            
            # Check specifically for suppliers and units tables
            if 'suppliers' not in tables:
                print('\n⚠️  suppliers table is missing!')
            if 'units' not in tables:
                print('\n⚠️  units table is missing!')
                
            return tables
    except Exception as e:
        print(f'❌ Error checking tables: {e}')
        return []

if __name__ == "__main__":
    check_tables()
