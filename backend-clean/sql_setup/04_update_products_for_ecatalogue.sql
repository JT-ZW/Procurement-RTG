-- ========================================
-- E-CATALOGUE MODULE 1 - PRODUCTS TABLE ENHANCEMENT
-- ========================================
-- This script adds the necessary fields for the E-catalogue functionality
-- to support comprehensive product management with inventory tracking

-- Add new columns to products table for E-catalogue functionality
ALTER TABLE products ADD COLUMN IF NOT EXISTS contract_price DECIMAL(10, 2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS current_stock_quantity DECIMAL(10, 3) DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS estimated_consumption_rate_per_day DECIMAL(10, 3) DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_id UUID REFERENCES units(id) ON DELETE SET NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS specifications JSONB;
ALTER TABLE products ADD COLUMN IF NOT EXISTS last_restocked_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS last_consumption_update TIMESTAMP WITH TIME ZONE;

-- Create additional indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_contract_price ON products(contract_price);
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_products_unit ON products(unit_id);
CREATE INDEX IF NOT EXISTS idx_products_stock_level ON products(current_stock_quantity);
CREATE INDEX IF NOT EXISTS idx_products_consumption_rate ON products(estimated_consumption_rate_per_day);

-- Create a view for E-catalogue with calculated fields
CREATE OR REPLACE VIEW e_catalogue_view AS
SELECT 
    p.id,
    p.name,
    p.code,
    p.description,
    p.category_id,
    pc.name AS category_name,
    pc.code AS category_code,
    p.unit_of_measure,
    p.standard_cost,
    p.contract_price,
    COALESCE(p.contract_price, p.standard_cost) AS effective_unit_price,
    p.currency,
    p.current_stock_quantity,
    p.minimum_stock_level,
    p.maximum_stock_level,
    p.reorder_point,
    p.estimated_consumption_rate_per_day,
    -- Calculate estimated days stock will last
    CASE 
        WHEN p.estimated_consumption_rate_per_day > 0 
        THEN ROUND(p.current_stock_quantity / p.estimated_consumption_rate_per_day, 2)
        ELSE NULL 
    END AS estimated_days_stock_will_last,
    -- Stock status indicator
    CASE 
        WHEN p.current_stock_quantity <= p.minimum_stock_level THEN 'LOW_STOCK'
        WHEN p.current_stock_quantity <= p.reorder_point THEN 'REORDER_NEEDED'
        WHEN p.current_stock_quantity >= p.maximum_stock_level THEN 'OVERSTOCK'
        ELSE 'NORMAL'
    END AS stock_status,
    p.supplier_id,
    s.name AS supplier_name,
    s.code AS supplier_code,
    p.unit_id,
    u.name AS unit_name,
    u.code AS unit_code,
    p.specifications,
    p.is_active,
    p.last_restocked_date,
    p.last_consumption_update,
    p.created_at,
    p.updated_at
FROM products p
LEFT JOIN product_categories pc ON p.category_id = pc.id
LEFT JOIN suppliers s ON p.supplier_id = s.id
LEFT JOIN units u ON p.unit_id = u.id
WHERE p.is_active = true;

-- Create additional indexes for stock status calculations
CREATE INDEX IF NOT EXISTS idx_products_stock_calculations ON products(current_stock_quantity, minimum_stock_level, reorder_point, maximum_stock_level) WHERE is_active = true;

-- Comment on the new columns
COMMENT ON COLUMN products.contract_price IS 'Contract price agreed with supplier (if different from standard cost)';
COMMENT ON COLUMN products.current_stock_quantity IS 'Current available stock quantity';
COMMENT ON COLUMN products.estimated_consumption_rate_per_day IS 'Estimated daily consumption rate for stock planning';
COMMENT ON COLUMN products.supplier_id IS 'Primary supplier for this product';
COMMENT ON COLUMN products.unit_id IS 'Unit/Hotel where this product is managed';
COMMENT ON COLUMN products.specifications IS 'Additional product specifications in JSON format';
COMMENT ON COLUMN products.last_restocked_date IS 'Date when stock was last replenished';
COMMENT ON COLUMN products.last_consumption_update IS 'Date when consumption rate was last updated';
