-- ========================================
-- HOTEL PROCUREMENT SYSTEM - USEFUL VIEWS
-- ========================================
-- This file creates views that provide useful data aggregations and reports

-- ========================================
-- 1. USER DASHBOARD VIEW
-- ========================================
CREATE OR REPLACE VIEW user_dashboard AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    ut.name AS unit_name,
    ut.code AS unit_code,
    -- Requisition counts
    COUNT(DISTINCT CASE WHEN pr.status = 'draft' THEN pr.id END) AS draft_requisitions,
    COUNT(DISTINCT CASE WHEN pr.status = 'submitted' THEN pr.id END) AS pending_requisitions,
    COUNT(DISTINCT CASE WHEN pr.status = 'approved' THEN pr.id END) AS approved_requisitions,
    -- Notification count
    COUNT(DISTINCT CASE WHEN n.is_read = false THEN n.id END) AS unread_notifications
FROM users u
LEFT JOIN units ut ON u.unit_id = ut.id
LEFT JOIN purchase_requisitions pr ON u.id = pr.requested_by
LEFT JOIN notifications n ON u.id = n.user_id AND n.is_read = false
WHERE u.is_active = true
GROUP BY u.id, u.email, u.first_name, u.last_name, u.role, ut.name, ut.code;

-- ========================================
-- 2. REQUISITION SUMMARY VIEW
-- ========================================
CREATE OR REPLACE VIEW requisition_summary AS
SELECT 
    pr.id,
    pr.requisition_number,
    pr.title,
    pr.department,
    pr.status,
    pr.priority,
    pr.requested_date,
    pr.required_date,
    pr.total_estimated_amount,
    pr.currency,
    -- User details
    u.first_name || ' ' || u.last_name AS requested_by_name,
    u.email AS requested_by_email,
    -- Unit details
    ut.name AS unit_name,
    ut.code AS unit_code,
    -- Approval details
    approver.first_name || ' ' || approver.last_name AS approved_by_name,
    pr.approved_at,
    -- Item counts
    COUNT(pri.id) AS total_items,
    SUM(pri.quantity) AS total_quantity,
    -- Days calculations
    CASE 
        WHEN pr.required_date < CURRENT_DATE THEN 'OVERDUE'
        WHEN pr.required_date = CURRENT_DATE THEN 'DUE TODAY'
        WHEN pr.required_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'DUE SOON'
        ELSE 'ON TIME'
    END AS urgency_status
FROM purchase_requisitions pr
JOIN users u ON pr.requested_by = u.id
JOIN units ut ON pr.unit_id = ut.id
LEFT JOIN users approver ON pr.approved_by = approver.id
LEFT JOIN purchase_requisition_items pri ON pr.id = pri.requisition_id
GROUP BY pr.id, pr.requisition_number, pr.title, pr.department, pr.status, pr.priority,
         pr.requested_date, pr.required_date, pr.total_estimated_amount, pr.currency,
         u.first_name, u.last_name, u.email, ut.name, ut.code,
         approver.first_name, approver.last_name, pr.approved_at;

-- ========================================
-- 3. PURCHASE ORDER TRACKING VIEW
-- ========================================
CREATE OR REPLACE VIEW purchase_order_tracking AS
SELECT 
    po.id,
    po.po_number,
    po.status,
    po.order_date,
    po.expected_delivery_date,
    po.actual_delivery_date,
    po.final_amount,
    po.currency,
    -- Supplier details
    s.name AS supplier_name,
    s.contact_person AS supplier_contact,
    s.email AS supplier_email,
    s.phone AS supplier_phone,
    -- Unit details
    ut.name AS unit_name,
    ut.code AS unit_code,
    -- Created by
    u.first_name || ' ' || u.last_name AS created_by_name,
    -- Delivery status
    CASE 
        WHEN po.actual_delivery_date IS NOT NULL THEN 'DELIVERED'
        WHEN po.expected_delivery_date < CURRENT_DATE THEN 'OVERDUE'
        WHEN po.expected_delivery_date = CURRENT_DATE THEN 'DUE TODAY'
        WHEN po.expected_delivery_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'DUE SOON'
        ELSE 'ON SCHEDULE'
    END AS delivery_status,
    -- Item summary
    COUNT(poi.id) AS total_items,
    SUM(poi.quantity) AS total_ordered_quantity,
    SUM(poi.received_quantity) AS total_received_quantity,
    ROUND(
        CASE 
            WHEN SUM(poi.quantity) > 0 THEN 
                (SUM(poi.received_quantity) / SUM(poi.quantity)) * 100
            ELSE 0 
        END, 2
    ) AS completion_percentage
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.id
JOIN units ut ON po.unit_id = ut.id
JOIN users u ON po.created_by = u.id
LEFT JOIN purchase_order_items poi ON po.id = poi.po_id
GROUP BY po.id, po.po_number, po.status, po.order_date, po.expected_delivery_date,
         po.actual_delivery_date, po.final_amount, po.currency,
         s.name, s.contact_person, s.email, s.phone,
         ut.name, ut.code, u.first_name, u.last_name;

-- ========================================
-- 4. INVENTORY NEEDS VIEW
-- ========================================
CREATE OR REPLACE VIEW inventory_needs AS
SELECT 
    p.id,
    p.name,
    p.code,
    p.description,
    pc.name AS category_name,
    p.unit_of_measure,
    p.standard_cost,
    p.minimum_stock_level,
    p.reorder_point,
    p.maximum_stock_level,
    -- Calculate current stock level (this would need integration with actual inventory)
    -- For now, we'll use a placeholder
    0 AS current_stock_level,
    -- Determine reorder status
    CASE 
        WHEN 0 <= p.minimum_stock_level THEN 'CRITICAL - REORDER IMMEDIATELY'
        WHEN 0 <= p.reorder_point THEN 'LOW - REORDER SOON'
        WHEN 0 >= p.maximum_stock_level THEN 'OVERSTOCK'
        ELSE 'NORMAL'
    END AS stock_status,
    -- Recent requisition activity
    COUNT(DISTINCT pri.requisition_id) AS recent_requisitions_count,
    SUM(pri.quantity) AS total_requested_quantity,
    MAX(pr.requested_date) AS last_requested_date
FROM products p
LEFT JOIN product_categories pc ON p.category_id = pc.id
LEFT JOIN purchase_requisition_items pri ON p.id = pri.product_id
LEFT JOIN purchase_requisitions pr ON pri.requisition_id = pr.id 
    AND pr.requested_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE p.is_active = true
GROUP BY p.id, p.name, p.code, p.description, pc.name, p.unit_of_measure,
         p.standard_cost, p.minimum_stock_level, p.reorder_point, p.maximum_stock_level;

-- ========================================
-- 5. SPENDING ANALYSIS VIEW
-- ========================================
CREATE OR REPLACE VIEW spending_analysis AS
SELECT 
    ut.id AS unit_id,
    ut.name AS unit_name,
    ut.code AS unit_code,
    EXTRACT(YEAR FROM pr.requested_date) AS year,
    EXTRACT(MONTH FROM pr.requested_date) AS month,
    TO_CHAR(pr.requested_date, 'YYYY-MM') AS period,
    -- Requisition counts by status
    COUNT(CASE WHEN pr.status = 'draft' THEN 1 END) AS draft_count,
    COUNT(CASE WHEN pr.status = 'submitted' THEN 1 END) AS submitted_count,
    COUNT(CASE WHEN pr.status = 'approved' THEN 1 END) AS approved_count,
    COUNT(CASE WHEN pr.status = 'rejected' THEN 1 END) AS rejected_count,
    -- Financial summary
    SUM(CASE WHEN pr.status IN ('submitted', 'approved', 'completed') THEN pr.total_estimated_amount ELSE 0 END) AS total_requested_amount,
    SUM(CASE WHEN pr.status = 'approved' THEN pr.total_estimated_amount ELSE 0 END) AS total_approved_amount,
    AVG(CASE WHEN pr.status IN ('submitted', 'approved', 'completed') THEN pr.total_estimated_amount END) AS avg_requisition_amount,
    -- Department breakdown would go here (requires department normalization)
    COUNT(DISTINCT pr.department) AS departments_count,
    COUNT(DISTINCT pr.requested_by) AS unique_requesters
FROM units ut
LEFT JOIN purchase_requisitions pr ON ut.id = pr.unit_id
WHERE ut.is_active = true
GROUP BY ut.id, ut.name, ut.code, 
         EXTRACT(YEAR FROM pr.requested_date),
         EXTRACT(MONTH FROM pr.requested_date),
         TO_CHAR(pr.requested_date, 'YYYY-MM')
ORDER BY ut.name, year DESC, month DESC;

-- ========================================
-- 6. SUPPLIER PERFORMANCE VIEW
-- ========================================
CREATE OR REPLACE VIEW supplier_performance AS
SELECT 
    s.id,
    s.name,
    s.code,
    s.contact_person,
    s.email,
    s.rating,
    -- Purchase order statistics
    COUNT(DISTINCT po.id) AS total_orders,
    SUM(po.final_amount) AS total_order_value,
    AVG(po.final_amount) AS avg_order_value,
    -- Delivery performance
    COUNT(CASE WHEN po.actual_delivery_date IS NOT NULL THEN 1 END) AS completed_deliveries,
    COUNT(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 END) AS on_time_deliveries,
    ROUND(
        CASE 
            WHEN COUNT(CASE WHEN po.actual_delivery_date IS NOT NULL THEN 1 END) > 0 THEN
                (COUNT(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 END)::DECIMAL / 
                 COUNT(CASE WHEN po.actual_delivery_date IS NOT NULL THEN 1 END)) * 100
            ELSE 0
        END, 2
    ) AS on_time_delivery_rate,
    -- Recent activity
    MAX(po.order_date) AS last_order_date,
    COUNT(CASE WHEN po.order_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) AS recent_orders,
    -- Quotation statistics
    COUNT(DISTINCT q.id) AS total_quotations,
    COUNT(CASE WHEN q.status = 'accepted' THEN 1 END) AS accepted_quotations,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT q.id) > 0 THEN
                (COUNT(CASE WHEN q.status = 'accepted' THEN 1 END)::DECIMAL / COUNT(DISTINCT q.id)) * 100
            ELSE 0
        END, 2
    ) AS quotation_success_rate
FROM suppliers s
LEFT JOIN purchase_orders po ON s.id = po.supplier_id
LEFT JOIN quotations q ON s.id = q.supplier_id
WHERE s.is_active = true
GROUP BY s.id, s.name, s.code, s.contact_person, s.email, s.rating
ORDER BY total_order_value DESC NULLS LAST;

-- ========================================
-- 7. APPROVAL WORKFLOW VIEW
-- ========================================
CREATE OR REPLACE VIEW approval_workflow AS
SELECT 
    pr.id AS requisition_id,
    pr.requisition_number,
    pr.title,
    pr.total_estimated_amount,
    pr.status AS current_status,
    -- Requester info
    requester.first_name || ' ' || requester.last_name AS requested_by,
    requester.email AS requester_email,
    pr.requested_date,
    -- Unit info
    ut.name AS unit_name,
    -- Approval chain
    ba.approval_level,
    ba.status AS approval_status,
    approver.first_name || ' ' || approver.last_name AS approver_name,
    approver.email AS approver_email,
    approver.role AS approver_role,
    ba.approved_amount,
    ba.comments AS approval_comments,
    ba.approved_at,
    -- Time in approval
    CASE 
        WHEN ba.approved_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (ba.approved_at - pr.created_at)) / 3600
        ELSE 
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - pr.created_at)) / 3600
    END AS hours_in_approval
FROM purchase_requisitions pr
JOIN users requester ON pr.requested_by = requester.id
JOIN units ut ON pr.unit_id = ut.id
LEFT JOIN budget_approvals ba ON pr.id = ba.requisition_id
LEFT JOIN users approver ON ba.approver_id = approver.id
WHERE pr.status IN ('submitted', 'under_review', 'approved', 'rejected')
ORDER BY pr.requested_date DESC, ba.approval_level;

-- ========================================
-- 8. MONTHLY PROCUREMENT REPORT VIEW
-- ========================================
CREATE OR REPLACE VIEW monthly_procurement_report AS
SELECT 
    TO_CHAR(DATE_TRUNC('month', pr.requested_date), 'YYYY-MM') AS month,
    ut.name AS unit_name,
    -- Request metrics
    COUNT(pr.id) AS total_requisitions,
    COUNT(CASE WHEN pr.status = 'approved' THEN 1 END) AS approved_requisitions,
    COUNT(CASE WHEN pr.status = 'rejected' THEN 1 END) AS rejected_requisitions,
    COUNT(CASE WHEN pr.status = 'completed' THEN 1 END) AS completed_requisitions,
    -- Financial metrics
    SUM(pr.total_estimated_amount) AS total_requested_value,
    SUM(CASE WHEN pr.status = 'approved' THEN pr.total_estimated_amount ELSE 0 END) AS total_approved_value,
    -- Purchase orders
    COUNT(DISTINCT po.id) AS purchase_orders_created,
    SUM(po.final_amount) AS total_po_value,
    -- Supplier metrics
    COUNT(DISTINCT po.supplier_id) AS unique_suppliers_used,
    -- Average processing time (in days)
    AVG(
        CASE 
            WHEN pr.approved_at IS NOT NULL THEN 
                EXTRACT(EPOCH FROM (pr.approved_at - pr.created_at)) / 86400
            ELSE NULL
        END
    ) AS avg_approval_days
FROM purchase_requisitions pr
JOIN units ut ON pr.unit_id = ut.id
LEFT JOIN purchase_orders po ON pr.id = po.requisition_id
WHERE pr.requested_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
GROUP BY DATE_TRUNC('month', pr.requested_date), ut.id, ut.name
ORDER BY month DESC, unit_name;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================
DO $$
BEGIN
    RAISE NOTICE 'Procurement system views created successfully!';
    RAISE NOTICE 'Available views:';
    RAISE NOTICE '- user_dashboard: User-specific dashboard data';
    RAISE NOTICE '- requisition_summary: Detailed requisition information';
    RAISE NOTICE '- purchase_order_tracking: PO status and delivery tracking';
    RAISE NOTICE '- inventory_needs: Products requiring reorder';
    RAISE NOTICE '- spending_analysis: Financial analysis by unit and period';
    RAISE NOTICE '- supplier_performance: Supplier metrics and ratings';
    RAISE NOTICE '- approval_workflow: Approval process tracking';
    RAISE NOTICE '- monthly_procurement_report: Monthly summary reports';
END $$;
