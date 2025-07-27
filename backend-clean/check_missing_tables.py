#!/usr/bin/env python3
"""
Check missing tables
"""
import os
from sqlalchemy import create_engine, text

database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password123@localhost:5432/procurement_db')
engine = create_engine(database_url)

with engine.connect() as conn:
    # Check if suppliers table exists
    result = conn.execute(text("""
        SELECT COUNT(*) as count FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'suppliers'
    """))
    suppliers_exists = result.first().count > 0
    print(f'Suppliers table exists: {suppliers_exists}')
    
    # Check if units table exists
    result = conn.execute(text("""
        SELECT COUNT(*) as count FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'units'
    """))
    units_exists = result.first().count > 0
    print(f'Units table exists: {units_exists}')
    
    if suppliers_exists:
        result = conn.execute(text('SELECT COUNT(*) as count FROM suppliers'))
        suppliers_count = result.first().count
        print(f'Suppliers in table: {suppliers_count}')
    
    if units_exists:
        result = conn.execute(text('SELECT COUNT(*) as count FROM units'))
        units_count = result.first().count
        print(f'Units in table: {units_count}')
