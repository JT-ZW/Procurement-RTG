#!/usr/bin/env python3
"""
Comprehensive Database Setup Tool for Procurement System
Handles existing Supabase data and provides multiple setup options
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    sys.exit(1)

class ProcurementDatabaseSetup:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, echo=False)
        
    def test_connection(self):
        """Test database connection"""
        print("🔌 Testing database connection...")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Connected to: {version}")
                return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False

    def inspect_existing_tables(self):
        """Inspect existing tables and data"""
        print("🔍 Inspecting existing database...")
        
        try:
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                
                print(f"📋 Found {len(tables)} existing tables:")
                table_info = {}
                
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        table_info[table] = count
                        print(f"   • {table}: {count} records")
                    except Exception as e:
                        table_info[table] = f"Error: {str(e)}"
                        print(f"   • {table}: Error reading")
                
                return table_info
                
        except Exception as e:
            print(f"❌ Error inspecting database: {str(e)}")
            return {}

    def backup_existing_data(self):
        """Create backup of existing data"""
        print("💾 Creating backup of existing data...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_supabase_data_{timestamp}.sql"
        
        try:
            with self.engine.connect() as conn:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write("-- Supabase Database Backup\n")
                    f.write(f"-- Created: {datetime.now()}\n")
                    f.write("-- Before Procurement System Setup\n\n")
                    
                    # Get all tables
                    inspector = inspect(self.engine)
                    tables = inspector.get_table_names()
                    
                    for table in tables:
                        try:
                            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = result.scalar()
                            
                            if count > 0:
                                f.write(f"-- Table: {table} ({count} records)\n")
                                
                                # Get table structure
                                columns = inspector.get_columns(table)
                                col_names = [col['name'] for col in columns]
                                
                                # Get data
                                result = conn.execute(text(f"SELECT * FROM {table}"))
                                rows = result.fetchall()
                                
                                for row in rows:
                                    values = []
                                    for i, col_name in enumerate(col_names):
                                        val = row[i]
                                        if val is None:
                                            values.append('NULL')
                                        elif isinstance(val, str):
                                            escaped_val = val.replace("'", "''")
                                            values.append(f"'{escaped_val}'")
                                        elif isinstance(val, datetime):
                                            values.append(f"'{val.isoformat()}'")
                                        else:
                                            values.append(str(val))
                                    
                                    f.write(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({', '.join(values)});\n")
                                
                                f.write("\n")
                                
                        except Exception as e:
                            f.write(f"-- Error backing up table {table}: {str(e)}\n")
            
            print(f"✅ Backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Error creating backup: {str(e)}")
            return None

    def clean_database(self):
        """Drop all existing tables"""
        print("🧹 Cleaning database (dropping all tables)...")
        
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                # Get all tables
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                
                # Drop in reverse order to handle dependencies
                for table in reversed(tables):
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                        print(f"   ✓ Dropped: {table}")
                    except Exception as e:
                        print(f"   ⚠️  Could not drop {table}: {str(e)}")
                
                trans.commit()
                print("✅ Database cleaned successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error cleaning database: {str(e)}")
            return False

    def setup_procurement_tables(self):
        """Create procurement system tables"""
        print("🏗️  Setting up procurement system tables...")
        
        try:
            with self.engine.connect() as conn:
                # Read table creation script
                if not os.path.exists('sql_setup/01_create_tables.sql'):
                    print("❌ Table creation script not found: sql_setup/01_create_tables.sql")
                    return False
                
                with open('sql_setup/01_create_tables.sql', 'r', encoding='utf-8') as f:
                    create_tables_sql = f.read()
                
                # Execute table creation
                conn.execute(text(create_tables_sql))
                conn.commit()
                
                print("✅ Procurement tables created successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")
            return False

    def insert_sample_data(self):
        """Insert sample data"""
        print("📊 Inserting sample data...")
        
        try:
            with self.engine.connect() as conn:
                # Read sample data script
                if not os.path.exists('sql_setup/02_insert_sample_data.sql'):
                    print("❌ Sample data script not found: sql_setup/02_insert_sample_data.sql")
                    return False
                
                with open('sql_setup/02_insert_sample_data.sql', 'r', encoding='utf-8') as f:
                    sample_data_sql = f.read()
                
                # Execute sample data insertion
                conn.execute(text(sample_data_sql))
                conn.commit()
                
                print("✅ Sample data inserted successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error inserting sample data: {str(e)}")
            return False

    def verify_setup(self):
        """Verify that setup was successful"""
        print("🔍 Verifying setup...")
        
        expected_tables = [
            'units', 'users', 'suppliers', 'product_categories', 
            'products', 'purchase_requisitions', 'purchase_requisition_items',
            'budget_approvals', 'purchase_orders', 'purchase_order_items',
            'notifications'
        ]
        
        try:
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                existing_tables = inspector.get_table_names()
                
                missing_tables = []
                for table in expected_tables:
                    if table not in existing_tables:
                        missing_tables.append(table)
                    else:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"   ✓ {table}: {count} records")
                
                if missing_tables:
                    print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
                    return False
                else:
                    print("✅ All expected tables found!")
                    return True
                    
        except Exception as e:
            print(f"❌ Error verifying setup: {str(e)}")
            return False

def main():
    """Main setup menu"""
    print("🏨 HOTEL PROCUREMENT SYSTEM - DATABASE SETUP")
    print("=" * 60)
    
    setup = ProcurementDatabaseSetup()
    
    # Test connection first
    if not setup.test_connection():
        print("❌ Cannot proceed without database connection.")
        return
    
    # Inspect existing data
    existing_tables = setup.inspect_existing_tables()
    
    if existing_tables:
        print(f"\n⚠️  Found {len(existing_tables)} existing tables with data.")
        print("Choose how to proceed:")
        print()
        print("1. 🧹 Clean Start (DELETE all existing data)")
        print("2. 💾 Backup First, then Clean Start")
        print("3. 🔍 Just Inspect (no changes)")
        print("4. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            if input("⚠️  This will DELETE ALL data. Type 'YES' to confirm: ") == 'YES':
                if setup.clean_database():
                    if setup.setup_procurement_tables():
                        if setup.insert_sample_data():
                            setup.verify_setup()
                            print("\n🎉 Fresh procurement system setup complete!")
                            print("\n📋 Sample Login Credentials:")
                            print("   • admin@hotel.com (password: password123)")
                            print("   • manager.ghd@hotel.com (password: password123)")
                            print("   • chef@hotel.com (password: password123)")
                else:
                    print("❌ Setup failed.")
            else:
                print("❌ Setup cancelled.")
                
        elif choice == '2':
            backup_file = setup.backup_existing_data()
            if backup_file:
                print(f"✅ Backup saved as: {backup_file}")
                if input("Proceed with clean setup? (y/N): ").lower() == 'y':
                    if setup.clean_database():
                        if setup.setup_procurement_tables():
                            if setup.insert_sample_data():
                                setup.verify_setup()
                                print("\n🎉 Setup complete with backup saved!")
            else:
                print("❌ Backup failed. Setup cancelled.")
                
        elif choice == '3':
            print("✅ Inspection complete. No changes made.")
            
        elif choice == '4':
            print("👋 Goodbye!")
            
        else:
            print("❌ Invalid choice.")
    
    else:
        # No existing tables, proceed with fresh setup
        print("✅ No existing tables found. Proceeding with fresh setup...")
        if setup.setup_procurement_tables():
            if setup.insert_sample_data():
                setup.verify_setup()
                print("\n🎉 Fresh procurement system setup complete!")

if __name__ == "__main__":
    main()
