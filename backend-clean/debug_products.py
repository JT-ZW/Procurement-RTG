#!/usr/bin/env python3
"""
Debug products endpoint
"""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def debug_products_query():
    async with AsyncSessionLocal() as session:
        print("Testing exact query from products endpoint...")
        
        # Test the exact query from the products endpoint
        query = """
        SELECT 
            id, name, code, description, category_id, unit_of_measure,
            standard_cost, contract_price, currency, 
            effective_unit_price,
            current_stock_quantity, minimum_stock_level, maximum_stock_level,
            reorder_point, estimated_consumption_rate_per_day,
            estimated_days_stock_will_last, stock_status,
            supplier_id, unit_id, specifications, is_active,
            last_restocked_date, last_consumption_update, created_at, updated_at,
            category_name, category_code, supplier_name, supplier_code, 
            unit_name, unit_code
        FROM e_catalogue_view
        WHERE is_active = true
        ORDER BY name LIMIT 5 OFFSET 0
        """
        
        try:
            result = await session.execute(text(query))
            rows = result.fetchall()
            print(f"Query succeeded! Found {len(rows)} rows")
            
            if rows:
                row = rows[0]
                print(f"First row data:")
                print(f"  ID: {row.id}")
                print(f"  Name: {row.name}")
                print(f"  Code: {row.code}")
                print(f"  Category ID: {row.category_id}")
                print(f"  Category Name: {row.category_name}")
                print(f"  Category Code: {row.category_code}")
                
        except Exception as e:
            print(f"Query failed: {e}")
            print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(debug_products_query())
