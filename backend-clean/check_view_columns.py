#!/usr/bin/env python3
"""
Check e_catalogue_view columns
"""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_view_columns():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'e_catalogue_view' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        columns = [row.column_name for row in result]
        print('Available columns in e_catalogue_view:')
        for col in columns:
            print(f'  • {col}')

if __name__ == "__main__":
    asyncio.run(check_view_columns())
