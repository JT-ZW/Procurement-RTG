"""
Admin Dashboard API Endpoints
Provides admin-specific operations for system management and statistics.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import os

from app.api.deps import get_db, get_current_user, get_current_active_superuser
from app.models.user import User, UserUnitAssignment
from app.models.unit import Unit
from app.models.product import Product, ProductUnitAllocation
from app.models.supplier import Supplier, SupplierUnitRelationship
from app.schemas.admin import (
    DashboardStats, SystemOverview, UnitStats, UserStats,
    AdminUserCreate, AdminUserUpdate, UnitConfigUpdate,
    SystemSettings
)
from app.utils.multi_tenant import get_user_units, get_unit_statistics_summary

router = APIRouter()

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Serve the admin dashboard HTML page.
    """
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@router.get("/dashboard/overview", response_model=SystemOverview)
async def get_system_overview(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> SystemOverview:
    """
    Get system overview statistics for admin dashboard.
    Only available to superusers.
    """
    # Get basic counts
    total_units = db.query(Unit).filter(Unit.is_deleted == False).count()
    active_units = db.query(Unit).filter(
        and_(Unit.is_active == True, Unit.is_deleted == False)
    ).count()
    
    total_users = db.query(User).filter(User.is_deleted == False).count()
    active_users = db.query(User).filter(
        and_(User.is_active == True, User.is_deleted == False)
    ).count()
    
    total_products = db.query(Product).filter(Product.is_deleted == False).count()
    total_suppliers = db.query(Supplier).filter(Supplier.is_deleted == False).count()
    
    # Get user assignments
    total_assignments = db.query(UserUnitAssignment).filter(
        UserUnitAssignment.is_active == True
    ).count()
    
    # Get recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    new_users_week = db.query(User).filter(
        User.created_at >= week_ago
    ).count()
    
    return SystemOverview(
        total_units=total_units,
        active_units=active_units,
        total_users=total_users,
        active_users=active_users,
        total_products=total_products,
        total_suppliers=total_suppliers,
        total_assignments=total_assignments,
        new_users_this_week=new_users_week
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics")
) -> DashboardStats:
    """
    Get dashboard statistics based on user's access level.
    """
    start_date = datetime.now() - timedelta(days=days)
    
    if current_user.is_superuser:
        # Superuser sees all system stats
        accessible_units = db.query(Unit.id).filter(Unit.is_deleted == False).all()
        unit_ids = [unit.id for unit in accessible_units]
    else:
        # Regular user sees only their accessible units
        unit_ids = get_user_units(db, current_user.id)
    
    # Get unit statistics
    unit_stats = []
    for unit_id in unit_ids:
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            continue
            
        # Get unit-specific counts
        products_count = db.query(ProductUnitAllocation).filter(
            ProductUnitAllocation.unit_id == unit_id
        ).count()
        
        suppliers_count = db.query(SupplierUnitRelationship).filter(
            and_(
                SupplierUnitRelationship.unit_id == unit_id,
                SupplierUnitRelationship.status == "active"
            )
        ).count()
        
        users_count = db.query(UserUnitAssignment).filter(
            and_(
                UserUnitAssignment.unit_id == unit_id,
                UserUnitAssignment.is_active == True
            )
        ).count()
        
        unit_stats.append(UnitStats(
            unit_id=unit_id,
            unit_name=unit.name,
            unit_code=unit.unit_code,
            products_count=products_count,
            suppliers_count=suppliers_count,
            users_count=users_count,
            is_active=unit.is_active
        ))
    
    return DashboardStats(
        period_days=days,
        units=unit_stats,
        total_accessible_units=len(unit_ids)
    )


@router.get("/units/{unit_id}/stats", response_model=UnitStats)
async def get_unit_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unit_id: str
) -> UnitStats:
    """
    Get detailed statistics for a specific unit.
    """
    # Check if user has access to this unit
    if not current_user.is_superuser:
        accessible_units = get_user_units(db, current_user.id)
        if unit_id not in [str(uid) for uid in accessible_units]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this unit"
            )
    
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Get detailed unit statistics
    products_count = db.query(ProductUnitAllocation).filter(
        ProductUnitAllocation.unit_id == unit_id
    ).count()
    
    low_stock_count = db.query(ProductUnitAllocation).filter(
        and_(
            ProductUnitAllocation.unit_id == unit_id,
            ProductUnitAllocation.current_stock <= ProductUnitAllocation.reorder_point
        )
    ).count()
    
    suppliers_count = db.query(SupplierUnitRelationship).filter(
        and_(
            SupplierUnitRelationship.unit_id == unit_id,
            SupplierUnitRelationship.status == "active"
        )
    ).count()
    
    users_count = db.query(UserUnitAssignment).filter(
        and_(
            UserUnitAssignment.unit_id == unit_id,
            UserUnitAssignment.is_active == True
        )
    ).count()
    
    return UnitStats(
        unit_id=unit_id,
        unit_name=unit.name,
        unit_code=unit.unit_code,
        products_count=products_count,
        suppliers_count=suppliers_count,
        users_count=users_count,
        low_stock_items=low_stock_count,
        is_active=unit.is_active,
        created_at=unit.created_at
    )


@router.get("/users/stats", response_model=UserStats)
async def get_user_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> UserStats:
    """
    Get user statistics across the system.
    Only available to superusers.
    """
    # Get role distribution
    role_stats = db.query(
        UserUnitAssignment.role,
        func.count(UserUnitAssignment.id).label('count')
    ).filter(
        UserUnitAssignment.is_active == True
    ).group_by(UserUnitAssignment.role).all()
    
    role_distribution = {stat.role: stat.count for stat in role_stats}
    
    # Get recent activity
    week_ago = datetime.now() - timedelta(days=7)
    month_ago = datetime.now() - timedelta(days=30)
    
    new_users_week = db.query(User).filter(User.created_at >= week_ago).count()
    new_users_month = db.query(User).filter(User.created_at >= month_ago).count()
    
    # Get active sessions (approximate - based on recent activity)
    active_sessions = db.query(User).filter(
        and_(
            User.is_active == True,
            User.last_login_at >= datetime.now() - timedelta(hours=24)
        )
    ).count() if hasattr(User, 'last_login_at') else 0
    
    return UserStats(
        total_users=db.query(User).filter(User.is_deleted == False).count(),
        active_users=db.query(User).filter(
            and_(User.is_active == True, User.is_deleted == False)
        ).count(),
        role_distribution=role_distribution,
        new_users_this_week=new_users_week,
        new_users_this_month=new_users_month,
        active_sessions=active_sessions
    )


@router.post("/users", response_model=Dict[str, Any])
async def create_admin_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    user_in: AdminUserCreate
) -> Dict[str, Any]:
    """
    Create a new user with admin privileges.
    Only available to superusers.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    from app.core.security import get_password_hash
    
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        title=user_in.title,
        department=user_in.department,
        phone=user_in.phone,
        role=user_in.role,
        is_superuser=user_in.is_superuser,
        is_active=user_in.is_active,
        created_by=current_user.id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create unit assignments if provided
    if user_in.unit_assignments:
        for assignment in user_in.unit_assignments:
            db_assignment = UserUnitAssignment(
                user_id=db_user.id,
                unit_id=assignment.unit_id,
                role=assignment.role,
                is_primary_unit=assignment.is_primary_unit,
                can_approve_orders=assignment.can_approve_orders,
                approval_limit=assignment.approval_limit,
                assigned_by=current_user.id
            )
            db.add(db_assignment)
    
    db.commit()
    
    return {
        "message": "User created successfully",
        "user_id": str(db_user.id),
        "email": db_user.email
    }


@router.put("/units/{unit_id}/config", response_model=Dict[str, Any])
async def update_unit_configuration(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unit_id: str,
    config_in: UnitConfigUpdate
) -> Dict[str, Any]:
    """
    Update unit configuration settings.
    """
    # Check access permissions
    if not current_user.is_superuser:
        # TODO: Check if user is unit manager
        pass
    
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Update unit configuration
    update_data = config_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(unit, field):
            setattr(unit, field, value)
    
    unit.updated_by = current_user.id
    db.commit()
    
    return {
        "message": "Unit configuration updated successfully",
        "unit_id": unit_id
    }


@router.get("/system/settings", response_model=SystemSettings)
async def get_system_settings(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> SystemSettings:
    """
    Get system-wide settings.
    Only available to superusers.
    """
    # This would typically come from a settings table or configuration
    # For now, return some basic system information
    
    return SystemSettings(
        system_name="Gateway Stream Procurement System",
        version="1.0.0",
        multi_tenant_enabled=True,
        total_units=db.query(Unit).count(),
        maintenance_mode=False,
        registration_enabled=True,
        password_policy={
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": False
        }
    )


@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get system health status.
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Get basic system stats
        total_users = db.query(User).count()
        total_units = db.query(Unit).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_users": total_users,
            "total_units": total_units,
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }
