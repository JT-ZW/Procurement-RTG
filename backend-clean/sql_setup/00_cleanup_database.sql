-- ========================================
-- SUPABASE DATABASE CLEANUP SCRIPT
-- ========================================
-- Run this in Supabase SQL Editor to clean your database
-- WARNING: This will delete ALL existing tables and data!

-- Step 1: Disable foreign key constraints temporarily
SET session_replication_role = replica;

-- Step 2: Drop all existing tables in public schema
DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Get all table names
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped table: %', r.tablename;
    END LOOP;
END $$;

-- Step 3: Re-enable foreign key constraints
SET session_replication_role = DEFAULT;

-- Step 4: Clean up any remaining sequences
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public')
    LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
        RAISE NOTICE 'Dropped sequence: %', r.sequence_name;
    END LOOP;
END $$;

-- Step 5: Enable UUID extension (required for our schema)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database cleanup completed successfully!';
    RAISE NOTICE '📋 Next steps:';
    RAISE NOTICE '1. Run the 01_create_tables.sql script';
    RAISE NOTICE '2. Run the 02_insert_sample_data.sql script';
    RAISE NOTICE '3. Test your application!';
END $$;
