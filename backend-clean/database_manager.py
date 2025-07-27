#!/usr/bin/env python3
"""
Database Management Tool for Supabase
Handles existing tables and provides clean setup options
"""
import os
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.connect_with_retry()
    
    def connect_with_retry(self, max_retries=3):
        """Connect to database with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempting database connection (attempt {attempt + 1}/{max_retries})...")
                self.engine = create_engine(DATABASE_URL, pool_timeout=30, pool_recycle=3600)
                
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    print("✅ Database connection successful!")
                    return True
                    
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1} failed: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    print("⏳ Waiting 5 seconds before retry...")
                    time.sleep(5)
                    
        print("❌ Failed to connect after all retries")
        return False
    
    def check_existing_tables(self):
        """Check what tables exist"""
        if not self.engine:
            return False
            
        try:
            with self.engine.connect() as connection:
                print("\n🔍 Checking existing tables...")
                
                # Get all tables
                result = connection.execute(text("""
                    SELECT schemaname, tablename, tableowner 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                """))
                
                tables = result.fetchall()
                
                if tables:
                    print(f"\n📋 Found {len(tables)} existing tables:")
                    print("-" * 60)
                    for table in tables:
                        print(f"  • {table[1]} (owner: {table[2]})")
                    
                    return [table[1] for table in tables]
                else:
                    print("✅ No existing tables found - database is clean!")
                    return []
                    
        except Exception as e:
            print(f"❌ Error checking tables: {e}")
            return None
    
    def drop_all_tables(self, confirm=False):
        """Drop all existing tables (DESTRUCTIVE)"""
        if not confirm:
            print("⚠️  This will DELETE ALL EXISTING TABLES!")
            response = input("Type 'YES' to confirm: ")
            if response != 'YES':
                print("❌ Operation cancelled")
                return False
        
        try:
            with self.engine.connect() as connection:
                # Get all tables
                result = connection.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                
                if not tables:
                    print("✅ No tables to drop")
                    return True
                
                print(f"\n🗑️  Dropping {len(tables)} tables...")
                
                # Disable foreign key checks temporarily
                connection.execute(text("SET session_replication_role = replica;"))
                
                # Drop each table
                for table in tables:
                    print(f"  • Dropping {table}...")
                    connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                
                # Re-enable foreign key checks
                connection.execute(text("SET session_replication_role = DEFAULT;"))
                
                connection.commit()
                print("✅ All tables dropped successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
            return False
    
    def create_clean_schema(self):
        """Create our procurement schema from scratch"""
        try:
            with self.engine.connect() as connection:
                print("\n🏗️  Creating clean procurement schema...")
                
                # Enable UUID extension
                connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                
                # Read and execute our schema
                schema_file = "sql_setup/01_create_tables.sql"
                if os.path.exists(schema_file):
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                    
                    # Execute schema creation
                    connection.execute(text(schema_sql))
                    connection.commit()
                    print("✅ Schema created successfully!")
                    return True
                else:
                    print(f"❌ Schema file not found: {schema_file}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error creating schema: {e}")
            return False
    
    def insert_sample_data(self):
        """Insert sample data"""
        try:
            with self.engine.connect() as connection:
                print("\n📝 Inserting sample data...")
                
                data_file = "sql_setup/02_insert_sample_data.sql"
                if os.path.exists(data_file):
                    with open(data_file, 'r') as f:
                        data_sql = f.read()
                    
                    # Execute data insertion
                    connection.execute(text(data_sql))
                    connection.commit()
                    print("✅ Sample data inserted successfully!")
                    return True
                else:
                    print(f"❌ Data file not found: {data_file}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error inserting data: {e}")
            return False

def main():
    print("="*60)
    print("🏨 HOTEL PROCUREMENT SYSTEM - DATABASE SETUP")
    print("="*60)
    
    db = DatabaseManager()
    
    if not db.engine:
        print("❌ Cannot proceed without database connection")
        return
    
    # Check existing tables
    existing_tables = db.check_existing_tables()
    
    if existing_tables is None:
        print("❌ Cannot check existing tables")
        return
    
    print("\n" + "="*60)
    print("SETUP OPTIONS:")
    print("="*60)
    print("1. 🗑️  Drop all existing tables and start fresh (DESTRUCTIVE)")
    print("2. 🏗️  Create schema only (if database is clean)")
    print("3. 📝 Insert sample data only (if schema exists)")
    print("4. 🔄 Full setup (drop + create + insert)")
    print("5. ❌ Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                if db.drop_all_tables():
                    print("✅ Database cleaned successfully!")
                break
                
            elif choice == '2':
                if db.create_clean_schema():
                    print("✅ Schema created successfully!")
                break
                
            elif choice == '3':
                if db.insert_sample_data():
                    print("✅ Sample data inserted successfully!")
                break
                
            elif choice == '4':
                print("\n🔄 Starting full setup...")
                if (db.drop_all_tables(confirm=True) and 
                    db.create_clean_schema() and 
                    db.insert_sample_data()):
                    print("\n🎉 Full setup completed successfully!")
                    print("\n📋 Next steps:")
                    print("1. Start your backend server")
                    print("2. Start your frontend application")
                    print("3. Login with: admin@hotel.com / password123")
                break
                
            elif choice == '5':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
