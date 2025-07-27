"""
Simple API endpoints for frontend integration
Returns data directly from the Supabase database using SQL queries
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import create_engine, text
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from app.core.security import get_current_user
from app.models.user import User

load_dotenv()

router = APIRouter()

# Create database engine
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL) if DATABASE_URL else None

def execute_query(query: str, params: dict = None) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results as list of dictionaries"""
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        columns = result.keys()
        rows = result.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]

@router.get("/units")
async def get_units(current_user: User = Depends(get_current_user)):
    """Get all hotel units"""
    query = """
        SELECT id::text, name, code, description, address, city, country, 
               is_active, created_at, updated_at
        FROM units 
        WHERE is_active = true
        ORDER BY name
    """
    return execute_query(query)

@router.get("/suppliers")
async def get_suppliers(current_user: User = Depends(get_current_user)):
    """Get all suppliers"""
    query = """
        SELECT id::text, name, code, contact_person, email, phone, address, 
               city, country, payment_terms, currency, rating, is_active,
               created_at, updated_at
        FROM suppliers 
        WHERE is_active = true
        ORDER BY name
    """
    return execute_query(query)

@router.get("/products")
async def get_products(current_user: User = Depends(get_current_user)):
    """Get all products with category information"""
    query = """
        SELECT p.id::text, p.name, p.code, p.description, 
               p.category_id::text, p.unit_of_measure,
               p.standard_cost, p.currency, p.minimum_stock_level, 
               p.maximum_stock_level, p.reorder_point, p.is_active,
               p.created_at, p.updated_at,
               pc.name as category_name, pc.code as category_code
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.is_active = true
        ORDER BY p.name
    """
    return execute_query(query)

@router.get("/product-categories")
async def get_product_categories(current_user: User = Depends(get_current_user)):
    """Get all product categories"""
    query = """
        SELECT id::text, name, code, description, parent_category_id::text, 
               is_active, created_at, updated_at
        FROM product_categories 
        WHERE is_active = true
        ORDER BY name
    """
    return execute_query(query)

@router.get("/purchase-requisitions")
async def get_purchase_requisitions(current_user: User = Depends(get_current_user)):
    """Get all purchase requisitions"""
    query = """
        SELECT pr.id::text, pr.requisition_number, pr.title, pr.description, 
               pr.department, pr.requested_by::text, pr.unit_id::text, 
               pr.priority, pr.status, pr.requested_date, pr.required_date,
               pr.total_estimated_amount, pr.currency, pr.approval_notes,
               pr.approved_by::text, pr.approved_at, pr.created_at, pr.updated_at,
               u.first_name || ' ' || u.last_name as requester_name,
               u.email as requester_email,
               unt.name as unit_name,
               app.first_name || ' ' || app.last_name as approver_name
        FROM purchase_requisitions pr
        LEFT JOIN users u ON pr.requested_by = u.id
        LEFT JOIN users app ON pr.approved_by = app.id
        LEFT JOIN units unt ON pr.unit_id = unt.id
        ORDER BY pr.created_at DESC
        LIMIT 100
    """
    return execute_query(query)

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    
    # Get requisition counts by status
    status_query = """
        SELECT status, COUNT(*) as count
        FROM purchase_requisitions
        GROUP BY status
    """
    status_data = execute_query(status_query)
    status_counts = {row['status']: row['count'] for row in status_data}
    
    # Get total counts
    totals_query = """
        SELECT 
            (SELECT COUNT(*) FROM purchase_requisitions) as total_requisitions,
            (SELECT COUNT(*) FROM products WHERE is_active = true) as total_products,
            (SELECT COUNT(*) FROM suppliers WHERE is_active = true) as total_suppliers,
            (SELECT COUNT(*) FROM units WHERE is_active = true) as total_units
    """
    totals_data = execute_query(totals_query)
    totals = totals_data[0] if totals_data else {}
    
    # Get urgent requisitions
    urgent_query = """
        SELECT COUNT(*) as urgent_count
        FROM purchase_requisitions
        WHERE priority IN ('urgent', 'high')
        AND status NOT IN ('completed', 'cancelled', 'rejected')
    """
    urgent_data = execute_query(urgent_query)
    urgent_count = urgent_data[0]['urgent_count'] if urgent_data else 0
    
    return {
        "total_requisitions": totals.get('total_requisitions', 0),
        "total_products": totals.get('total_products', 0),
        "total_suppliers": totals.get('total_suppliers', 0),
        "total_units": totals.get('total_units', 0),
        "status_counts": status_counts,
        "urgent_count": urgent_count,
        "pending_approval": status_counts.get('submitted', 0) + status_counts.get('under_review', 0)
    }

@router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Get user notifications"""
    query = """
        SELECT id::text, title, message, type, related_entity_type,
               related_entity_id::text, is_read, created_at, read_at
        FROM notifications
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 50
    """
    return execute_query(query, {"user_id": current_user.id})

@router.get("/admin/dashboard-stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics for admin users"""
    # Check if user has admin permissions
    if current_user.role not in ['admin', 'superuser', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Get counts for all major entities
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM products WHERE is_active = true) as total_products,
                (SELECT COUNT(*) FROM suppliers WHERE is_active = true) as total_suppliers,
                (SELECT COUNT(*) FROM units WHERE is_active = true) as total_units,
                (SELECT COUNT(*) FROM users WHERE is_active = true) as total_users,
                (SELECT COUNT(*) FROM purchase_requisitions) as total_requisitions
        """
        
        stats_result = execute_query(stats_query)
        stats = stats_result[0] if stats_result else {}
        
        # Get requisition status counts
        status_query = """
            SELECT status, COUNT(*) as count
            FROM purchase_requisitions
            GROUP BY status
        """
        status_result = execute_query(status_query)
        status_counts = {row['status']: row['count'] for row in status_result}
        
        # Get urgent requisitions count
        urgent_query = """
            SELECT COUNT(*) as count
            FROM purchase_requisitions
            WHERE priority IN ('urgent', 'high')
            AND status NOT IN ('completed', 'cancelled', 'rejected')
        """
        urgent_result = execute_query(urgent_query)
        urgent_count = urgent_result[0]['count'] if urgent_result else 0
        
        return {
            "total_products": stats.get('total_products', 0),
            "total_suppliers": stats.get('total_suppliers', 0),
            "total_units": stats.get('total_units', 0),
            "total_users": stats.get('total_users', 0),
            "total_requisitions": stats.get('total_requisitions', 0),
            "status_counts": status_counts,
            "urgent_count": urgent_count,
            "pending_approval": status_counts.get('submitted', 0) + status_counts.get('under_review', 0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/admin/reset-password")
async def reset_user_password(
    user_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Reset user password (Admin only)"""
    # Check if user has admin permissions
    if current_user.role not in ['admin', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reset passwords"
        )
    
    user_id = user_data.get("user_id")
    new_password = user_data.get("new_password", "newpassword123")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )
    
    try:
        # Hash the new password
        import bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user password
        update_query = """
            UPDATE users 
            SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
        """
        
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        with engine.connect() as conn:
            result = conn.execute(text(update_query), {
                "password_hash": hashed_password,
                "user_id": user_id
            })
            conn.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        return {
            "message": "Password reset successfully",
            "user_id": user_id,
            "new_password": new_password  # In production, don't return this
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@router.post("/change-password")
async def change_own_password(
    password_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Change own password"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both current_password and new_password are required"
        )
    
    try:
        import bcrypt
        
        # Get current password hash
        check_query = """
            SELECT password_hash FROM users WHERE id = :user_id
        """
        result = execute_query(check_query, {"user_id": str(current_user.id)})
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        current_hash = result[0]['password_hash']
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), current_hash.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        update_query = """
            UPDATE users 
            SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
        """
        
        with engine.connect() as conn:
            conn.execute(text(update_query), {
                "password_hash": new_hash,
                "user_id": str(current_user.id)
            })
            conn.commit()
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.post("/auth/password-reset")
async def request_password_reset(email_data: dict):
    """Request password reset for a user"""
    email = email_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    try:
        # Check if user exists
        user_query = """
            SELECT id::text, email, first_name, last_name
            FROM users
            WHERE email = :email AND is_active = true
        """
        user_result = execute_query(user_query, {"email": email})
        
        if not user_result:
            # Don't reveal if user exists or not for security
            return {
                "message": "If the email exists in our system, you will receive a password reset link",
                "status": "sent"
            }
        
        user = user_result[0]
        
        # In a real system, you would:
        # 1. Generate a secure reset token
        # 2. Store it in database with expiration
        # 3. Send email with reset link
        
        # For demo purposes, we'll simulate this
        import uuid
        reset_token = str(uuid.uuid4())
        
        return {
            "message": "Password reset instructions sent to your email",
            "status": "sent",
            "reset_token": reset_token,  # In production, don't return this
            "user_id": user['id']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset error: {str(e)}"
        )

@router.get("/admin/units/configuration")
async def get_units_configuration(current_user: User = Depends(get_current_user)):
    """Get detailed unit configuration (Admin only)"""
    if current_user.role not in ['admin', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view unit configuration"
        )
    
    try:
        # Get basic unit info first
        units_query = """
            SELECT 
                id::text,
                name,
                code,
                description,
                address,
                city,
                country,
                is_active,
                created_at,
                updated_at
            FROM units
            ORDER BY name
        """
        
        units = execute_query(units_query)
        
        # Add stats for each unit
        for unit in units:
            unit_id = unit['id']
            
            # Get user count
            user_count_query = """
                SELECT COUNT(*) as count FROM users WHERE unit_id = :unit_id
            """
            user_result = execute_query(user_count_query, {"unit_id": unit_id})
            unit['user_count'] = user_result[0]['count'] if user_result else 0
            
            # Get product count (if products table has unit_id)
            try:
                product_count_query = """
                    SELECT COUNT(*) as count FROM products WHERE unit_id = :unit_id
                """
                product_result = execute_query(product_count_query, {"unit_id": unit_id})
                unit['product_count'] = product_result[0]['count'] if product_result else 0
            except:
                unit['product_count'] = 0
            
            # Get requisition count
            req_count_query = """
                SELECT COUNT(*) as count FROM purchase_requisitions WHERE unit_id = :unit_id
            """
            req_result = execute_query(req_count_query, {"unit_id": unit_id})
            unit['requisition_count'] = req_result[0]['count'] if req_result else 0
        
        return units
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unit configuration: {str(e)}"
        )

@router.post("/admin/units/configure")
async def configure_unit(
    unit_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update unit configuration (Admin only)"""
    if current_user.role not in ['admin', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can configure units"
        )
    
    unit_id = unit_data.get("unit_id")
    if not unit_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unit_id is required"
        )
    
    try:
        # Update unit configuration
        update_query = """
            UPDATE units 
            SET 
                name = COALESCE(:name, name),
                description = COALESCE(:description, description),
                address = COALESCE(:address, address),
                city = COALESCE(:city, city),
                country = COALESCE(:country, country),
                is_active = COALESCE(:is_active, is_active),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :unit_id
        """
        
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        with engine.connect() as conn:
            result = conn.execute(text(update_query), {
                "unit_id": unit_id,
                "name": unit_data.get("name"),
                "description": unit_data.get("description"),
                "address": unit_data.get("address"),
                "city": unit_data.get("city"),
                "country": unit_data.get("country"),
                "is_active": unit_data.get("is_active")
            })
            conn.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Unit not found"
                )
        
        return {"message": "Unit configuration updated successfully", "unit_id": unit_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unit configuration failed: {str(e)}"
        )

@router.get("/admin/system-settings")
async def get_system_settings(current_user: User = Depends(get_current_user)):
    """Get system-wide settings (Admin only)"""
    if current_user.role not in ['admin', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view system settings"
        )
    
    try:
        # Get system statistics and settings
        system_query = """
            SELECT 
                'system_info' as setting_type,
                COUNT(DISTINCT u.id) as total_units,
                COUNT(DISTINCT us.id) as total_users,
                COUNT(DISTINCT p.id) as total_products,
                COUNT(DISTINCT s.id) as total_suppliers,
                COUNT(DISTINCT pr.id) as total_requisitions,
                MAX(pr.created_at) as last_requisition_date,
                MAX(us.created_at) as last_user_created
            FROM units u
            CROSS JOIN users us
            CROSS JOIN products p
            CROSS JOIN suppliers s
            CROSS JOIN purchase_requisitions pr
        """
        
        settings = execute_query(system_query)
        
        # Add version and configuration info
        system_info = settings[0] if settings else {}
        system_info.update({
            "app_version": "1.0.0",
            "database_type": "PostgreSQL (Supabase)",
            "authentication": "JWT Bearer Token",
            "multi_tenant": True,
            "features_enabled": [
                "Multi-tenant Units",
                "Role-based Access Control", 
                "Product Management",
                "Supplier Management",
                "Purchase Requisitions",
                "Dashboard Analytics",
                "User Management",
                "Password Reset"
            ]
        })
        
        return system_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system settings: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    query = """
        SELECT id::text, email, first_name, last_name, role, unit_id::text,
               is_active, is_superuser, created_at, updated_at
        FROM users
        WHERE id = :user_id
    """
    result = execute_query(query, {"user_id": str(current_user.id)})
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data = result[0]
    
    # Get unit name if unit_id exists
    if user_data.get('unit_id'):
        unit_query = """
            SELECT name
            FROM units
            WHERE id = :unit_id
        """
        unit_result = execute_query(unit_query, {"unit_id": user_data['unit_id']})
        user_data['unit_name'] = unit_result[0]['name'] if unit_result else None
    else:
        user_data['unit_name'] = None
    
    return user_data

@router.post("/suppliers")
async def create_supplier_simple(
    supplier_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier"""
    # Check if user has permission (only managers and superusers)
    if current_user.role not in ['manager', 'superuser']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    import uuid
    new_id = str(uuid.uuid4())
    
    # Insert new supplier
    insert_query = """
        INSERT INTO suppliers (id, name, code, contact_person, email, phone, address, 
                             city, country, payment_terms, currency, rating)
        VALUES (:id, :name, :code, :contact_person, :email, :phone, :address, 
                :city, :country, :payment_terms, :currency, :rating)
    """
    
    params = {
        "id": new_id,
        "name": supplier_data.get("name"),
        "code": supplier_data.get("code"),
        "contact_person": supplier_data.get("contact_person"),
        "email": supplier_data.get("email"),
        "phone": supplier_data.get("phone"),
        "address": supplier_data.get("address"),
        "city": supplier_data.get("city"),
        "country": supplier_data.get("country"),
        "payment_terms": supplier_data.get("payment_terms", "Net 30"),
        "currency": supplier_data.get("currency", "USD"),
        "rating": supplier_data.get("rating", 5)
    }
    
    try:
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        with engine.connect() as conn:
            conn.execute(text(insert_query), params)
            conn.commit()
        
        # Return the created supplier
        get_query = """
            SELECT id::text, name, code, contact_person, email, phone, address, city, country,
                   tax_number, payment_terms, credit_limit, currency, rating, is_active,
                   created_at, updated_at
            FROM suppliers 
            WHERE id = :supplier_id
        """
        result = execute_query(get_query, {"supplier_id": new_id})
        
        if result:
            return result[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created supplier"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
