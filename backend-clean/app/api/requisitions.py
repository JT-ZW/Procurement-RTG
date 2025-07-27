"""
Purchase Requisitions API endpoints for the Hotel Procurement System
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.requisition import PurchaseRequisition, PurchaseRequisitionCreate, PurchaseRequisitionUpdate

router = APIRouter()

@router.get("/", response_model=List[PurchaseRequisition])
async def get_purchase_requisitions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    unit_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all purchase requisitions"""
    from sqlalchemy import text
    
    base_query = """
        SELECT pr.id, pr.requisition_number, pr.title, pr.description, pr.department,
               pr.requested_by, pr.unit_id, pr.priority, pr.status, pr.requested_date,
               pr.required_date, pr.total_estimated_amount, pr.currency, pr.approval_notes,
               pr.approved_by, pr.approved_at, pr.created_at, pr.updated_at,
               u.first_name || ' ' || u.last_name as requester_name,
               u.email as requester_email,
               unt.name as unit_name,
               app.first_name || ' ' || app.last_name as approver_name
        FROM purchase_requisitions pr
        LEFT JOIN users u ON pr.requested_by = u.id
        LEFT JOIN users app ON pr.approved_by = app.id
        LEFT JOIN units unt ON pr.unit_id = unt.id
        WHERE 1=1
    """
    
    params = {"limit": limit, "skip": skip}
    
    if status_filter:
        base_query += " AND pr.status = :status_filter"
        params["status_filter"] = status_filter
    
    if unit_id:
        base_query += " AND pr.unit_id = :unit_id"
        params["unit_id"] = unit_id
    
    # Filter by user's unit if not superuser
    if current_user.role not in ['superuser']:
        base_query += " AND pr.unit_id = :user_unit_id"
        params["user_unit_id"] = str(current_user.unit_id) if current_user.unit_id else None
    
    base_query += " ORDER BY pr.created_at DESC LIMIT :limit OFFSET :skip"
    
    result = db.execute(text(base_query), params)
    
    requisitions = []
    for row in result:
        requisitions.append({
            "id": str(row.id),
            "requisition_number": row.requisition_number,
            "title": row.title,
            "description": row.description,
            "department": row.department,
            "requested_by": str(row.requested_by),
            "requester_name": row.requester_name,
            "requester_email": row.requester_email,
            "unit_id": str(row.unit_id),
            "unit_name": row.unit_name,
            "priority": row.priority,
            "status": row.status,
            "requested_date": row.requested_date.isoformat() if row.requested_date else None,
            "required_date": row.required_date.isoformat() if row.required_date else None,
            "total_estimated_amount": float(row.total_estimated_amount) if row.total_estimated_amount else 0.0,
            "currency": row.currency,
            "approval_notes": row.approval_notes,
            "approved_by": str(row.approved_by) if row.approved_by else None,
            "approver_name": row.approver_name,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
    
    return requisitions

@router.get("/{requisition_id}", response_model=PurchaseRequisition)
async def get_purchase_requisition(
    requisition_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific purchase requisition by ID"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT pr.id, pr.requisition_number, pr.title, pr.description, pr.department,
               pr.requested_by, pr.unit_id, pr.priority, pr.status, pr.requested_date,
               pr.required_date, pr.total_estimated_amount, pr.currency, pr.approval_notes,
               pr.approved_by, pr.approved_at, pr.created_at, pr.updated_at,
               u.first_name || ' ' || u.last_name as requester_name,
               u.email as requester_email,
               unt.name as unit_name,
               app.first_name || ' ' || app.last_name as approver_name
        FROM purchase_requisitions pr
        LEFT JOIN users u ON pr.requested_by = u.id
        LEFT JOIN users app ON pr.approved_by = app.id
        LEFT JOIN units unt ON pr.unit_id = unt.id
        WHERE pr.id = :requisition_id
    """), {"requisition_id": str(requisition_id)})
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase requisition not found"
        )
    
    # Check if user has access to this requisition
    if current_user.role not in ['superuser'] and str(row.unit_id) != str(current_user.unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this requisition"
        )
    
    # Get requisition items
    items_result = db.execute(text("""
        SELECT pri.id, pri.product_id, pri.product_name, pri.product_description,
               pri.quantity, pri.unit_of_measure, pri.estimated_unit_price,
               pri.estimated_total_price, pri.currency, pri.specifications, pri.notes,
               p.name as product_catalog_name, p.code as product_code
        FROM purchase_requisition_items pri
        LEFT JOIN products p ON pri.product_id = p.id
        WHERE pri.requisition_id = :requisition_id
        ORDER BY pri.created_at
    """), {"requisition_id": str(requisition_id)})
    
    items = []
    for item_row in items_result:
        items.append({
            "id": str(item_row.id),
            "product_id": str(item_row.product_id) if item_row.product_id else None,
            "product_name": item_row.product_name,
            "product_description": item_row.product_description,
            "product_catalog_name": item_row.product_catalog_name,
            "product_code": item_row.product_code,
            "quantity": float(item_row.quantity),
            "unit_of_measure": item_row.unit_of_measure,
            "estimated_unit_price": float(item_row.estimated_unit_price) if item_row.estimated_unit_price else None,
            "estimated_total_price": float(item_row.estimated_total_price) if item_row.estimated_total_price else None,
            "currency": item_row.currency,
            "specifications": item_row.specifications,
            "notes": item_row.notes
        })
    
    requisition_data = {
        "id": str(row.id),
        "requisition_number": row.requisition_number,
        "title": row.title,
        "description": row.description,
        "department": row.department,
        "requested_by": str(row.requested_by),
        "requester_name": row.requester_name,
        "requester_email": row.requester_email,
        "unit_id": str(row.unit_id),
        "unit_name": row.unit_name,
        "priority": row.priority,
        "status": row.status,
        "requested_date": row.requested_date.isoformat() if row.requested_date else None,
        "required_date": row.required_date.isoformat() if row.required_date else None,
        "total_estimated_amount": float(row.total_estimated_amount) if row.total_estimated_amount else 0.0,
        "currency": row.currency,
        "approval_notes": row.approval_notes,
        "approved_by": str(row.approved_by) if row.approved_by else None,
        "approver_name": row.approver_name,
        "approved_at": row.approved_at.isoformat() if row.approved_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "items": items
    }
    
    return requisition_data

@router.get("/stats/dashboard", response_model=dict)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for purchase requisitions"""
    from sqlalchemy import text
    
    # Base filter by unit if not superuser
    unit_filter = ""
    params = {}
    if current_user.role not in ['superuser'] and current_user.unit_id:
        unit_filter = "WHERE unit_id = :unit_id"
        params["unit_id"] = str(current_user.unit_id)
    
    # Get status counts
    status_result = db.execute(text(f"""
        SELECT status, COUNT(*) as count
        FROM purchase_requisitions
        {unit_filter}
        GROUP BY status
    """), params)
    
    status_counts = {}
    total_requisitions = 0
    for row in status_result:
        status_counts[row.status] = row.count
        total_requisitions += row.count
    
    # Get monthly trends (last 6 months)
    monthly_result = db.execute(text(f"""
        SELECT 
            DATE_TRUNC('month', requested_date) as month,
            COUNT(*) as count,
            SUM(total_estimated_amount) as total_amount
        FROM purchase_requisitions
        {unit_filter}
        WHERE requested_date >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY DATE_TRUNC('month', requested_date)
        ORDER BY month
    """), params)
    
    monthly_data = []
    for row in monthly_result:
        monthly_data.append({
            "month": row.month.strftime("%Y-%m") if row.month else None,
            "count": row.count,
            "total_amount": float(row.total_amount) if row.total_amount else 0.0
        })
    
    # Get urgent/high priority count
    urgent_result = db.execute(text(f"""
        SELECT COUNT(*) as count
        FROM purchase_requisitions
        {unit_filter}
        {"AND" if unit_filter else "WHERE"} priority IN ('urgent', 'high')
        AND status NOT IN ('completed', 'cancelled', 'rejected')
    """), params)
    
    urgent_count = urgent_result.scalar() or 0
    
    return {
        "total_requisitions": total_requisitions,
        "status_counts": status_counts,
        "urgent_count": urgent_count,
        "monthly_trends": monthly_data,
        "pending_approval": status_counts.get('submitted', 0) + status_counts.get('under_review', 0)
    }
