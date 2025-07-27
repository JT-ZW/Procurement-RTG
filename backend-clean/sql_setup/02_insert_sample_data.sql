-- ========================================
-- HOTEL PROCUREMENT SYSTEM - SAMPLE DATA
-- ========================================
-- This file inserts sample data for testing the procurement system
-- Run this after executing 01_create_tables.sql

-- ========================================
-- 1. INSERT SAMPLE UNITS (Hotels/Properties)
-- ========================================
INSERT INTO units (id, name, code, description, address, city, country) VALUES
(uuid_generate_v4(), 'Grand Hotel Downtown', 'GHD001', 'Luxury downtown hotel with 200 rooms', '123 Main Street', 'New York', 'USA'),
(uuid_generate_v4(), 'Seaside Resort & Spa', 'SRS002', 'Beachfront resort with spa facilities', '456 Ocean Drive', 'Miami', 'USA'),
(uuid_generate_v4(), 'Mountain View Lodge', 'MVL003', 'Cozy mountain lodge with 50 rooms', '789 Alpine Way', 'Denver', 'USA')
ON CONFLICT (code) DO NOTHING;

-- ========================================
-- 2. INSERT SAMPLE SUPPLIERS
-- ========================================
INSERT INTO suppliers (id, name, code, contact_person, email, phone, address, city, country, payment_terms, currency, rating) VALUES
(uuid_generate_v4(), 'Premium Food Distributors', 'PFD001', 'John Smith', 'orders@premiumfood.com', '+1-555-0101', '100 Food Plaza', 'New York', 'USA', 'Net 30', 'USD', 5),
(uuid_generate_v4(), 'Hotel Supplies Inc.', 'HSI002', 'Sarah Johnson', 'sales@hotelsupplies.com', '+1-555-0102', '200 Supply Street', 'Chicago', 'USA', 'Net 15', 'USD', 4),
(uuid_generate_v4(), 'Luxury Linens Co.', 'LLC003', 'Mike Wilson', 'info@luxurylinens.com', '+1-555-0103', '300 Textile Ave', 'Los Angeles', 'USA', 'Net 45', 'USD', 5),
(uuid_generate_v4(), 'Fresh Produce Partners', 'FPP004', 'Lisa Brown', 'orders@freshproduce.com', '+1-555-0104', '400 Market Road', 'Miami', 'USA', 'Net 7', 'USD', 4),
(uuid_generate_v4(), 'Maintenance Solutions Ltd.', 'MSL005', 'David Taylor', 'service@maintenance.com', '+1-555-0105', '500 Service Blvd', 'Denver', 'USA', 'Net 30', 'USD', 3)
ON CONFLICT (code) DO NOTHING;

-- ========================================
-- 3. INSERT PRODUCT CATEGORIES
-- ========================================
INSERT INTO product_categories (id, name, code, description) VALUES
(uuid_generate_v4(), 'Food & Beverage', 'FB001', 'All food and beverage items'),
(uuid_generate_v4(), 'Housekeeping Supplies', 'HK001', 'Cleaning supplies, linens, and room amenities'),
(uuid_generate_v4(), 'Maintenance & Engineering', 'ME001', 'Tools, parts, and maintenance supplies'),
(uuid_generate_v4(), 'Office Supplies', 'OS001', 'Stationery, electronics, and office equipment'),
(uuid_generate_v4(), 'Guest Amenities', 'GA001', 'Items provided directly to guests')
ON CONFLICT (code) DO NOTHING;

-- Get category IDs for foreign key references
DO $$
DECLARE
    fb_cat_id UUID;
    hk_cat_id UUID;
    me_cat_id UUID;
    os_cat_id UUID;
    ga_cat_id UUID;
BEGIN
    SELECT id INTO fb_cat_id FROM product_categories WHERE code = 'FB001';
    SELECT id INTO hk_cat_id FROM product_categories WHERE code = 'HK001';
    SELECT id INTO me_cat_id FROM product_categories WHERE code = 'ME001';
    SELECT id INTO os_cat_id FROM product_categories WHERE code = 'OS001';
    SELECT id INTO ga_cat_id FROM product_categories WHERE code = 'GA001';

    -- ========================================
    -- 4. INSERT SAMPLE PRODUCTS
    -- ========================================
    INSERT INTO products (id, name, code, description, category_id, unit_of_measure, standard_cost, minimum_stock_level, reorder_point) VALUES
    -- Food & Beverage
    (uuid_generate_v4(), 'Premium Coffee Beans', 'FB-COFFEE-001', 'Arabica coffee beans - 1kg bags', fb_cat_id, 'kg', 25.00, 50, 20),
    (uuid_generate_v4(), 'Fresh Orange Juice', 'FB-JUICE-001', 'Fresh squeezed orange juice - 1L bottles', fb_cat_id, 'bottles', 8.50, 100, 30),
    (uuid_generate_v4(), 'Premium Steak', 'FB-MEAT-001', 'USDA Prime ribeye steaks', fb_cat_id, 'kg', 45.00, 20, 10),
    (uuid_generate_v4(), 'White Wine', 'FB-WINE-001', 'Chardonnay white wine bottles', fb_cat_id, 'bottles', 18.00, 50, 15),
    
    -- Housekeeping Supplies
    (uuid_generate_v4(), 'Luxury Bath Towels', 'HK-TOWEL-001', '100% cotton bath towels - white', hk_cat_id, 'pieces', 12.00, 200, 50),
    (uuid_generate_v4(), 'Bed Sheets Set', 'HK-SHEET-001', 'Egyptian cotton sheet sets - queen size', hk_cat_id, 'sets', 35.00, 100, 25),
    (uuid_generate_v4(), 'All-Purpose Cleaner', 'HK-CLEAN-001', 'Multi-surface cleaning solution - 5L', hk_cat_id, 'bottles', 15.00, 50, 20),
    (uuid_generate_v4(), 'Toilet Paper', 'HK-PAPER-001', '3-ply toilet paper rolls', hk_cat_id, 'rolls', 2.50, 500, 100),
    
    -- Maintenance & Engineering
    (uuid_generate_v4(), 'HVAC Filter', 'ME-FILTER-001', 'High-efficiency air filters', me_cat_id, 'pieces', 22.00, 30, 10),
    (uuid_generate_v4(), 'LED Light Bulbs', 'ME-BULB-001', 'Energy efficient LED bulbs - 60W equivalent', me_cat_id, 'pieces', 8.00, 100, 25),
    (uuid_generate_v4(), 'Plumbing Repair Kit', 'ME-PLUMB-001', 'Complete plumbing repair toolkit', me_cat_id, 'kits', 85.00, 10, 5),
    
    -- Office Supplies
    (uuid_generate_v4(), 'Copy Paper', 'OS-PAPER-001', 'A4 white copy paper - 500 sheets', os_cat_id, 'reams', 6.50, 100, 30),
    (uuid_generate_v4(), 'Black Ink Cartridge', 'OS-INK-001', 'Printer ink cartridge - black', os_cat_id, 'pieces', 45.00, 20, 8),
    
    -- Guest Amenities
    (uuid_generate_v4(), 'Luxury Soap Set', 'GA-SOAP-001', 'Premium guest bathroom soap set', ga_cat_id, 'sets', 8.50, 200, 50),
    (uuid_generate_v4(), 'Welcome Fruit Basket', 'GA-FRUIT-001', 'Fresh fruit welcome basket for VIP guests', ga_cat_id, 'baskets', 25.00, 20, 10)
    ON CONFLICT (code) DO NOTHING;
END $$;

-- ========================================
-- 5. INSERT SAMPLE USERS
-- ========================================
-- Note: Passwords are hashed versions of 'password123'
DO $$
DECLARE
    unit1_id UUID;
    unit2_id UUID;
    unit3_id UUID;
BEGIN
    SELECT id INTO unit1_id FROM units WHERE code = 'GHD001';
    SELECT id INTO unit2_id FROM units WHERE code = 'SRS002';
    SELECT id INTO unit3_id FROM units WHERE code = 'MVL003';

    INSERT INTO users (id, email, hashed_password, first_name, last_name, phone, role, unit_id) VALUES
    -- Superuser
    (uuid_generate_v4(), 'admin@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'System', 'Administrator', '+1-555-0001', 'superuser', unit1_id),
    
    -- Hotel Managers
    (uuid_generate_v4(), 'manager.ghd@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'Alice', 'Johnson', '+1-555-1001', 'manager', unit1_id),
    (uuid_generate_v4(), 'manager.srs@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'Bob', 'Williams', '+1-555-1002', 'manager', unit2_id),
    (uuid_generate_v4(), 'manager.mvl@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'Carol', 'Davis', '+1-555-1003', 'manager', unit3_id),
    
    -- Department Staff
    (uuid_generate_v4(), 'chef@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'David', 'Miller', '+1-555-2001', 'staff', unit1_id),
    (uuid_generate_v4(), 'housekeeper@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'Emma', 'Garcia', '+1-555-2002', 'staff', unit1_id),
    (uuid_generate_v4(), 'maintenance@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'Frank', 'Rodriguez', '+1-555-2003', 'staff', unit2_id),
    (uuid_generate_v4(), 'procurement@hotel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW', 'Grace', 'Lopez', '+1-555-2004', 'staff', unit1_id)
    ON CONFLICT (email) DO NOTHING;
END $$;

-- ========================================
-- 6. INSERT SAMPLE PURCHASE REQUISITIONS
-- ========================================
DO $$
DECLARE
    chef_user_id UUID;
    housekeeper_user_id UUID;
    unit1_id UUID;
    unit2_id UUID;
    coffee_product_id UUID;
    towel_product_id UUID;
BEGIN
    SELECT id INTO chef_user_id FROM users WHERE email = 'chef@hotel.com';
    SELECT id INTO housekeeper_user_id FROM users WHERE email = 'housekeeper@hotel.com';
    SELECT id INTO unit1_id FROM units WHERE code = 'GHD001';
    SELECT id INTO unit2_id FROM units WHERE code = 'SRS002';
    SELECT id INTO coffee_product_id FROM products WHERE code = 'FB-COFFEE-001';
    SELECT id INTO towel_product_id FROM products WHERE code = 'HK-TOWEL-001';

    -- Insert sample requisitions
    INSERT INTO purchase_requisitions (id, requisition_number, title, description, department, requested_by, unit_id, priority, status, requested_date, required_date, total_estimated_amount) VALUES
    (uuid_generate_v4(), 'REQ-2025-001', 'Kitchen Supplies - Weekly Order', 'Weekly order for kitchen supplies and ingredients', 'Kitchen', chef_user_id, unit1_id, 'high', 'submitted', CURRENT_DATE, CURRENT_DATE + INTERVAL '3 days', 500.00),
    (uuid_generate_v4(), 'REQ-2025-002', 'Housekeeping Linens Restock', 'Monthly restock of towels and bed linens', 'Housekeeping', housekeeper_user_id, unit1_id, 'medium', 'approved', CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE + INTERVAL '7 days', 800.00),
    (uuid_generate_v4(), 'REQ-2025-003', 'Emergency Maintenance Supplies', 'Urgent order for HVAC filters and repair materials', 'Maintenance', housekeeper_user_id, unit2_id, 'urgent', 'under_review', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 day', 350.00)
    ON CONFLICT (requisition_number) DO NOTHING;

    -- Get requisition IDs for items
    DECLARE
        req1_id UUID;
        req2_id UUID;
    BEGIN
        SELECT id INTO req1_id FROM purchase_requisitions WHERE requisition_number = 'REQ-2025-001';
        SELECT id INTO req2_id FROM purchase_requisitions WHERE requisition_number = 'REQ-2025-002';

        -- Insert requisition items
        INSERT INTO purchase_requisition_items (id, requisition_id, product_id, product_name, quantity, unit_of_measure, estimated_unit_price, estimated_total_price) VALUES
        (uuid_generate_v4(), req1_id, coffee_product_id, 'Premium Coffee Beans', 10, 'kg', 25.00, 250.00),
        (uuid_generate_v4(), req1_id, (SELECT id FROM products WHERE code = 'FB-JUICE-001'), 'Fresh Orange Juice', 20, 'bottles', 8.50, 170.00),
        (uuid_generate_v4(), req2_id, towel_product_id, 'Luxury Bath Towels', 50, 'pieces', 12.00, 600.00),
        (uuid_generate_v4(), req2_id, (SELECT id FROM products WHERE code = 'HK-SHEET-001'), 'Bed Sheets Set', 10, 'sets', 35.00, 350.00);
    END;
END $$;

-- ========================================
-- 7. INSERT SAMPLE NOTIFICATIONS
-- ========================================
DO $$
DECLARE
    manager_user_id UUID;
    chef_user_id UUID;
BEGIN
    SELECT id INTO manager_user_id FROM users WHERE email = 'manager.ghd@hotel.com';
    SELECT id INTO chef_user_id FROM users WHERE email = 'chef@hotel.com';

    INSERT INTO notifications (id, user_id, title, message, type, related_entity_type) VALUES
    (uuid_generate_v4(), manager_user_id, 'New Requisition Pending', 'REQ-2025-001 requires your approval', 'warning', 'requisition'),
    (uuid_generate_v4(), chef_user_id, 'Requisition Approved', 'Your requisition REQ-2025-002 has been approved', 'success', 'requisition'),
    (uuid_generate_v4(), manager_user_id, 'Budget Alert', 'Monthly procurement budget is 80% utilized', 'info', 'budget');
END $$;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================
DO $$
BEGIN
    RAISE NOTICE 'Sample data inserted successfully!';
    RAISE NOTICE 'Login credentials (all passwords are "password123"):';
    RAISE NOTICE '- admin@hotel.com (Superuser)';
    RAISE NOTICE '- manager.ghd@hotel.com (Manager)';
    RAISE NOTICE '- chef@hotel.com (Staff)';
    RAISE NOTICE '- housekeeper@hotel.com (Staff)';
    RAISE NOTICE 'You can now test your procurement system!';
END $$;
