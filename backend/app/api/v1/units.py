from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_unit, crud_user
from app.models.user import User
from app.models.unit import Unit
from app.schemas.unit import (
    UnitCreate, 
    UnitUpdate, 
    UnitResponse, 
    UnitListResponse,
    UnitConfigUpdate,
    UnitConfigResponse,
    UnitUserAssignment,
    UnitUserResponse,
    UnitStatsResponse,
    UnitBudgetUpdate,
    UnitBudgetResponse
)
from app.utils.multi_tenant import check_unit_access, get_user_units, is_unit_manager

router = APIRouter()


@router.get("/", response_model=UnitListResponse)
def read_units(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    include_inactive: bool = Query(False, description="Include inactive units"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
) -> Any:
    """
    Retrieve units accessible to current user.
    """
    if current_user.is_superuser:
        # Superusers can see all units
        units, total = crud_unit.get_multi_with_filters(
            db,
            include_inactive=include_inactive,
            skip=skip,
            limit=limit
        )
    else:
        # Regular users only see their assigned units
        user_unit_ids = get_user_units(db, user_id=current_user.id)
        if not user_unit_ids:
            return {"items": [], "total": 0}
        
        units, total = crud_unit.get_multi_by_ids(
            db,
            unit_ids=user_unit_ids,
            include_inactive=include_inactive,
            skip=skip,
            limit=limit
        )
    
    return {"items": units, "total": total}


@router.post("/", response_model=UnitResponse)
def create_unit(
    unit_in: UnitCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create new hotel unit. Only accessible by superusers.
    """
    # Check if unit code already exists
    existing_unit = crud_unit.get_by_code(db, unit_code=unit_in.unit_code)
    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit with this code already exists"
        )
    
    unit = crud_unit.create(db, obj_in=unit_in)
    return unit


@router.get("/{unit_id}", response_model=UnitResponse)
def read_unit(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get unit by ID.
    """
    unit = crud_unit.get(db, id=unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Check access
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    return unit


@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: UUID,
    unit_in: UnitUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update unit. Accessible by superusers or unit managers.
    """
    unit = crud_unit.get(db, id=unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Check permissions - superuser or unit manager can update
    if not current_user.is_superuser:
        if not is_unit_manager(db, user=current_user, unit_id=unit_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this unit"
            )
    
    # If updating unit code, check for conflicts
    if unit_in.unit_code and unit_in.unit_code != unit.unit_code:
        existing_unit = crud_unit.get_by_code(db, unit_code=unit_in.unit_code)
        if existing_unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit with this code already exists"
            )
    
    unit = crud_unit.update(db, db_obj=unit, obj_in=unit_in)
    return unit


@router.delete("/{unit_id}")
def delete_unit(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Delete unit (soft delete). Only accessible by superusers.
    """
    unit = crud_unit.get(db, id=unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    # Check if unit has active data (products, orders, etc.)
    if crud_unit.has_active_dependencies(db, unit_id=unit_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete unit with active products, orders, or users"
        )
    
    crud_unit.remove(db, id=unit_id)
    return {"message": "Unit deleted successfully"}


# Unit Configuration Management
@router.get("/{unit_id}/config", response_model=UnitConfigResponse)
def read_unit_config(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get unit configuration settings.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    config = crud_unit.get_config(db, unit_id=unit_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit configuration not found"
        )
    
    return config


@router.put("/{unit_id}/config", response_model=UnitConfigResponse)
def update_unit_config(
    unit_id: UUID,
    config_in: UnitConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update unit configuration. Accessible by superusers or unit managers.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    if not current_user.is_superuser:
        if not is_unit_manager(db, user=current_user, unit_id=unit_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update unit configuration"
            )
    
    config = crud_unit.update_config(db, unit_id=unit_id, obj_in=config_in)
    return config


# Unit Budget Management
@router.get("/{unit_id}/budget", response_model=UnitBudgetResponse)
def read_unit_budget(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    year: Optional[int] = Query(None, description="Budget year")
) -> Any:
    """
    Get unit budget information.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    budget = crud_unit.get_budget(db, unit_id=unit_id, year=year)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit budget not found"
        )
    
    return budget


@router.put("/{unit_id}/budget", response_model=UnitBudgetResponse)
def update_unit_budget(
    unit_id: UUID,
    budget_in: UnitBudgetUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update unit budget. Accessible by superusers or unit managers.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    if not current_user.is_superuser:
        if not is_unit_manager(db, user=current_user, unit_id=unit_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update unit budget"
            )
    
    budget = crud_unit.update_budget(db, unit_id=unit_id, obj_in=budget_in)
    return budget


# Unit User Management
@router.get("/{unit_id}/users", response_model=List[UnitUserResponse])
def read_unit_users(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: bool = Query(True, description="Filter by active status")
) -> Any:
    """
    Get users assigned to unit.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    users = crud_unit.get_unit_users(
        db, 
        unit_id=unit_id, 
        role=role, 
        is_active=is_active
    )
    return users


@router.post("/{unit_id}/users", response_model=UnitUserResponse)
def assign_user_to_unit(
    unit_id: UUID,
    assignment: UnitUserAssignment,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Assign user to unit. Accessible by superusers or unit managers.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    if not current_user.is_superuser:
        if not is_unit_manager(db, user=current_user, unit_id=unit_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to assign users to this unit"
            )
    
    # Verify user exists
    user = crud_user.get(db, id=assignment.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if assignment already exists
    existing = crud_unit.get_user_unit_assignment(
        db, 
        user_id=assignment.user_id, 
        unit_id=unit_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already assigned to this unit"
        )
    
    assignment_result = crud_unit.assign_user_to_unit(
        db, 
        user_id=assignment.user_id, 
        unit_id=unit_id, 
        role=assignment.role
    )
    return assignment_result


@router.put("/{unit_id}/users/{user_id}")
def update_user_unit_assignment(
    unit_id: UUID,
    user_id: UUID,
    assignment: UnitUserAssignment,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update user's role in unit.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    if not current_user.is_superuser:
        if not is_unit_manager(db, user=current_user, unit_id=unit_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update user assignments"
            )
    
    assignment_result = crud_unit.update_user_unit_assignment(
        db, 
        user_id=user_id, 
        unit_id=unit_id, 
        role=assignment.role
    )
    
    if not assignment_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assignment not found"
        )
    
    return assignment_result


@router.delete("/{unit_id}/users/{user_id}")
def remove_user_from_unit(
    unit_id: UUID,
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Remove user from unit.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    if not current_user.is_superuser:
        if not is_unit_manager(db, user=current_user, unit_id=unit_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to remove users from this unit"
            )
    
    # Prevent removing the last manager
    if is_unit_manager(db, user_id=user_id, unit_id=unit_id):
        managers_count = crud_unit.count_unit_managers(db, unit_id=unit_id)
        if managers_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last manager from unit"
            )
    
    success = crud_unit.remove_user_from_unit(db, user_id=user_id, unit_id=unit_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assignment not found"
        )
    
    return {"message": "User removed from unit successfully"}


# Unit Statistics and Dashboard Data
@router.get("/{unit_id}/stats", response_model=UnitStatsResponse)
def read_unit_stats(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    period: str = Query("month", regex="^(week|month|quarter|year)$", description="Stats period")
) -> Any:
    """
    Get unit statistics for dashboard.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    stats = crud_unit.get_unit_statistics(db, unit_id=unit_id, period=period)
    return stats


@router.post("/{unit_id}/switch")
def switch_to_unit(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Switch user's active unit context.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    # Update user's current unit preference
    crud_user.update_current_unit(db, user_id=current_user.id, unit_id=unit_id)
    
    return {
        "message": "Successfully switched to unit",
        "unit_id": unit_id,
        "unit": crud_unit.get(db, id=unit_id)
    }


@router.get("/{unit_id}/dashboard")
def read_unit_dashboard(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get comprehensive dashboard data for unit.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    dashboard_data = {
        "unit": crud_unit.get(db, id=unit_id),
        "stats": crud_unit.get_unit_statistics(db, unit_id=unit_id, period="month"),
        "recent_orders": crud_unit.get_recent_orders(db, unit_id=unit_id, limit=10),
        "low_stock_alerts": crud_unit.get_low_stock_alerts(db, unit_id=unit_id),
        "pending_approvals": crud_unit.get_pending_approvals(db, unit_id=unit_id),
        "budget_status": crud_unit.get_budget_status(db, unit_id=unit_id),
        "supplier_performance": crud_unit.get_supplier_performance_summary(db, unit_id=unit_id)
    }
    
    return dashboard_data


# Unit Performance Reports
@router.get("/{unit_id}/performance")
def read_unit_performance(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    metrics: Optional[str] = Query("all", description="Comma-separated metrics to include")
) -> Any:
    """
    Get detailed unit performance report.
    """
    check_unit_access(db, user=current_user, unit_id=unit_id)
    
    performance_data = crud_unit.get_performance_report(
        db,
        unit_id=unit_id,
        start_date=start_date,
        end_date=end_date,
        metrics=metrics.split(",") if metrics != "all" else None
    )
    
    return performance_data