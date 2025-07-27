"""
Multi-tenant utilities for the procurement system.
Handles access control, data isolation, and unit-based permissions across 8 hotel units.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.user import User, UserUnitAssignment
from app.models.unit import Unit


def get_user_units(db: Session, user_id: UUID) -> List[UUID]:
    """
    Get list of unit IDs that a user has access to.
    
    Args:
        db: Database session
        user_id: User's UUID
        
    Returns:
        List of unit UUIDs the user can access
    """
    # Superusers have access to all units
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    if user.is_superuser:
        # Get all active units
        units = db.query(Unit.id).filter(
            and_(
                Unit.is_active == True,
                Unit.is_deleted == False
            )
        ).all()
        return [unit.id for unit in units]
    
    # Get units from user assignments
    assignments = db.query(UserUnitAssignment.unit_id).filter(
        and_(
            UserUnitAssignment.user_id == user_id,
            UserUnitAssignment.is_active == True
        )
    ).all()
    
    return [assignment.unit_id for assignment in assignments]


def check_unit_access(db: Session, user: User, unit_id: UUID) -> bool:
    """
    Check if a user has access to a specific unit.
    Raises HTTPException if access is denied.
    
    Args:
        db: Database session
        user: User object
        unit_id: Unit UUID to check access for
        
    Raises:
        HTTPException: If user doesn't have access to the unit
        
    Returns:
        True if access is granted
    """
    # Superusers have access to all units
    if user.is_superuser:
        return True
    
    # Check if unit exists and is active
    unit = db.query(Unit).filter(
        and_(
            Unit.id == unit_id,
            Unit.is_active == True,
            Unit.is_deleted == False
        )
    ).first()
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or inactive"
        )
    
    # Check user's unit assignments
    assignment = db.query(UserUnitAssignment).filter(
        and_(
            UserUnitAssignment.user_id == user.id,
            UserUnitAssignment.unit_id == unit_id,
            UserUnitAssignment.is_active == True
        )
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User not assigned to this unit"
        )
    
    return True


def is_unit_manager(db: Session, user: User = None, user_id: UUID = None, unit_id: UUID = None) -> bool:
    """
    Check if a user is a manager of any unit or a specific unit.
    
    Args:
        db: Database session
        user: User object (optional if user_id provided)
        user_id: User UUID (optional if user provided)
        unit_id: Specific unit to check (optional - checks any unit if not provided)
        
    Returns:
        True if user is a unit manager
    """
    if user:
        user_id = user.id
    elif not user_id:
        return False
    
    # Superusers are considered managers of all units
    if user and user.is_superuser:
        return True
    
    # Build query conditions
    conditions = [
        UserUnitAssignment.user_id == user_id,
        UserUnitAssignment.is_active == True,
        UserUnitAssignment.role.in_(["unit_manager", "store_manager"])
    ]
    
    if unit_id:
        conditions.append(UserUnitAssignment.unit_id == unit_id)
    
    assignment = db.query(UserUnitAssignment).filter(and_(*conditions)).first()
    return assignment is not None


def get_user_role_in_unit(db: Session, user_id: UUID, unit_id: UUID) -> Optional[str]:
    """
    Get user's role in a specific unit.
    
    Args:
        db: Database session
        user_id: User UUID
        unit_id: Unit UUID
        
    Returns:
        User's role in the unit or None if no assignment
    """
    assignment = db.query(UserUnitAssignment).filter(
        and_(
            UserUnitAssignment.user_id == user_id,
            UserUnitAssignment.unit_id == unit_id,
            UserUnitAssignment.is_active == True
        )
    ).first()
    
    return assignment.role if assignment else None


def can_manage_user(db: Session, manager: User, target_user: User) -> bool:
    """
    Check if one user can manage another user based on hierarchy and unit assignments.
    
    Args:
        db: Database session
        manager: User attempting to manage
        target_user: User being managed
        
    Returns:
        True if manager can manage target_user
    """
    # Superusers can manage everyone
    if manager.is_superuser:
        return True
    
    # Procurement admins can manage non-superusers
    if manager.role == "procurement_admin" and not target_user.is_superuser:
        return True
    
    # Users cannot manage themselves (for role/status changes)
    if manager.id == target_user.id:
        return False
    
    # Check if manager has management role in any unit where target user is assigned
    manager_units = get_managed_units(db, manager.id)
    target_units = get_user_units(db, target_user.id)
    
    # Check if there's overlap and manager has higher role
    common_units = set(manager_units) & set(target_units)
    
    for unit_id in common_units:
        manager_role = get_user_role_in_unit(db, manager.id, unit_id)
        target_role = get_user_role_in_unit(db, target_user.id, unit_id)
        
        # Define role hierarchy (higher number = higher role)
        role_hierarchy = {
            "store_staff": 1,
            "store_manager": 2,
            "unit_manager": 3
        }
        
        manager_level = role_hierarchy.get(manager_role, 0)
        target_level = role_hierarchy.get(target_role, 0)
        
        if manager_level > target_level:
            return True
    
    return False


def get_managed_units(db: Session, user_id: UUID) -> List[UUID]:
    """
    Get list of unit IDs that a user manages.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        List of unit UUIDs the user manages
    """
    assignments = db.query(UserUnitAssignment.unit_id).filter(
        and_(
            UserUnitAssignment.user_id == user_id,
            UserUnitAssignment.is_active == True,
            UserUnitAssignment.role.in_(["unit_manager", "store_manager"])
        )
    ).all()
    
    return [assignment.unit_id for assignment in assignments]


def has_unit_permission(
    db: Session, 
    user_id: UUID, 
    unit_id: UUID, 
    permission: str
) -> bool:
    """
    Check if user has a specific permission in a unit.
    
    Args:
        db: Database session
        user_id: User UUID
        unit_id: Unit UUID
        permission: Permission to check (e.g., 'can_approve_orders')
        
    Returns:
        True if user has the permission
    """
    assignment = db.query(UserUnitAssignment).filter(
        and_(
            UserUnitAssignment.user_id == user_id,
            UserUnitAssignment.unit_id == unit_id,
            UserUnitAssignment.is_active == True
        )
    ).first()
    
    if not assignment:
        return False
    
    # Check if the permission attribute exists and is True
    return getattr(assignment, permission, False)


def get_user_approval_limit(db: Session, user_id: UUID, unit_id: UUID) -> float:
    """
    Get user's approval limit for a specific unit.
    
    Args:
        db: Database session
        user_id: User UUID
        unit_id: Unit UUID
        
    Returns:
        Approval limit amount
    """
    assignment = db.query(UserUnitAssignment).filter(
        and_(
            UserUnitAssignment.user_id == user_id,
            UserUnitAssignment.unit_id == unit_id,
            UserUnitAssignment.is_active == True
        )
    ).first()
    
    return float(assignment.approval_limit) if assignment else 0.0


def validate_unit_assignment(
    db: Session, 
    user_id: UUID, 
    unit_id: UUID, 
    role: str
) -> Dict[str, Any]:
    """
    Validate a unit assignment before creation.
    
    Args:
        db: Database session
        user_id: User UUID
        unit_id: Unit UUID
        role: Role to assign
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        result["valid"] = False
        result["errors"].append("User not found")
        return result
    
    # Check if unit exists
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        result["valid"] = False
        result["errors"].append("Unit not found")
        return result
    
    if not unit.is_active:
        result["valid"] = False
        result["errors"].append("Unit is inactive")
        return result
    
    # Check if assignment already exists
    existing = db.query(UserUnitAssignment).filter(
        and_(
            UserUnitAssignment.user_id == user_id,
            UserUnitAssignment.unit_id == unit_id,
            UserUnitAssignment.is_active == True
        )
    ).first()
    
    if existing:
        result["valid"] = False
        result["errors"].append("User already assigned to this unit")
        return result
    
    # Validate role
    valid_roles = ["unit_manager", "store_manager", "store_staff", "supplier_liaison"]
    if role not in valid_roles:
        result["valid"] = False
        result["errors"].append(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return result
    
    # Check role hierarchy constraints
    if role == "unit_manager":
        # Check if there's already a unit manager
        existing_manager = db.query(UserUnitAssignment).filter(
            and_(
                UserUnitAssignment.unit_id == unit_id,
                UserUnitAssignment.role == "unit_manager",
                UserUnitAssignment.is_active == True
            )
        ).first()
        
        if existing_manager:
            result["warnings"].append("Unit already has a unit manager")
    
    return result


def get_unit_hierarchy(db: Session, user: User) -> Dict[str, Any]:
    """
    Get organizational hierarchy visible to the user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        Dictionary with unit hierarchy and user's position
    """
    hierarchy = {
        "user_role": user.role,
        "is_superuser": user.is_superuser,
        "accessible_units": [],
        "managed_units": [],
        "total_units": 0
    }
    
    # Get accessible units
    accessible_unit_ids = get_user_units(db, user.id)
    
    # Get unit details
    units = db.query(Unit).filter(
        and_(
            Unit.id.in_(accessible_unit_ids),
            Unit.is_active == True,
            Unit.is_deleted == False
        )
    ).all()
    
    hierarchy["accessible_units"] = [
        {
            "id": str(unit.id),
            "name": unit.name,
            "code": unit.unit_code,
            "city": unit.city,
            "status": unit.status,
            "user_role": get_user_role_in_unit(db, user.id, unit.id)
        }
        for unit in units
    ]
    
    # Get managed units
    if not user.is_superuser:
        managed_unit_ids = get_managed_units(db, user.id)
        hierarchy["managed_units"] = [
            unit for unit in hierarchy["accessible_units"] 
            if UUID(unit["id"]) in managed_unit_ids
        ]
    else:
        hierarchy["managed_units"] = hierarchy["accessible_units"]
    
    # Get total units count (for superusers)
    if user.is_superuser:
        hierarchy["total_units"] = db.query(Unit).filter(
            and_(
                Unit.is_active == True,
                Unit.is_deleted == False
            )
        ).count()
    else:
        hierarchy["total_units"] = len(hierarchy["accessible_units"])
    
    return hierarchy


def filter_query_by_unit_access(query, user: User, unit_ids: List[UUID], unit_field_name: str = "unit_id"):
    """
    Filter a SQLAlchemy query by unit access.
    
    Args:
        query: SQLAlchemy query object
        user: User object
        unit_ids: List of accessible unit IDs
        unit_field_name: Name of the unit field in the query model
        
    Returns:
        Filtered query
    """
    if user.is_superuser:
        return query  # Superusers see everything
    
    if not unit_ids:
        # User has no unit access - return empty result
        return query.filter(False)
    
    # Filter by accessible units
    return query.filter(getattr(query.column_descriptions[0]['type'], unit_field_name).in_(unit_ids))


def switch_unit_context(db: Session, user_id: UUID, unit_id: UUID) -> Dict[str, Any]:
    """
    Switch user's active unit context with validation.
    
    Args:
        db: Database session
        user_id: User UUID
        unit_id: Target unit UUID
        
    Returns:
        Dictionary with switch results
    """
    result = {
        "success": False,
        "message": "",
        "unit_info": None
    }
    
    # Verify user has access to the unit
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        result["message"] = "User not found"
        return result
    
    try:
        check_unit_access(db, user, unit_id)
    except HTTPException as e:
        result["message"] = e.detail
        return result
    
    # Get unit information
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        result["message"] = "Unit not found"
        return result
    
    # Update user's current unit preference
    if not user.preferences:
        user.preferences = {}
    
    user.preferences["current_unit_id"] = str(unit_id)
    user.preferences["last_unit_switch"] = datetime.utcnow().isoformat()
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        result["success"] = True
        result["message"] = f"Successfully switched to {unit.name}"
        result["unit_info"] = {
            "id": str(unit.id),
            "name": unit.name,
            "code": unit.unit_code,
            "city": unit.city,
            "user_role": get_user_role_in_unit(db, user_id, unit_id)
        }
        
    except Exception as e:
        db.rollback()
        result["message"] = f"Error switching unit context: {str(e)}"
    
    return result


def get_current_unit_context(user: User) -> Optional[UUID]:
    """
    Get user's current active unit context.
    
    Args:
        user: User object
        
    Returns:
        Current unit UUID or None
    """
    if user.preferences and "current_unit_id" in user.preferences:
        try:
            return UUID(user.preferences["current_unit_id"])
        except (ValueError, TypeError):
            pass
    
    return None


def validate_cross_unit_operation(
    db: Session,
    user: User,
    source_unit_id: UUID,
    target_unit_id: UUID,
    operation: str
) -> Dict[str, Any]:
    """
    Validate operations that span multiple units.
    
    Args:
        db: Database session
        user: User object
        source_unit_id: Source unit UUID
        target_unit_id: Target unit UUID
        operation: Type of operation ('transfer', 'compare', 'consolidate')
        
    Returns:
        Validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check access to both units
    try:
        check_unit_access(db, user, source_unit_id)
        check_unit_access(db, user, target_unit_id)
    except HTTPException as e:
        result["valid"] = False
        result["errors"].append(f"Unit access denied: {e.detail}")
        return result
    
    # Check if user has management rights for transfer operations
    if operation == "transfer":
        if not (is_unit_manager(db, user, unit_id=source_unit_id) or user.is_superuser):
            result["valid"] = False
            result["errors"].append("Transfer operations require management rights in source unit")
    
    # Add operation-specific validations
    if operation == "consolidate":
        if not (user.is_superuser or user.role == "procurement_admin"):
            result["valid"] = False
            result["errors"].append("Consolidation operations require admin privileges")
    
    return result


def get_unit_statistics_summary(db: Session, user: User) -> Dict[str, Any]:
    """
    Get summary statistics for units accessible to the user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        Statistics summary
    """
    accessible_units = get_user_units(db, user.id)
    
    if not accessible_units:
        return {
            "total_units": 0,
            "active_units": 0,
            "managed_units": 0,
            "units_by_status": {},
            "units_by_country": {}
        }
    
    # Get unit statistics
    units = db.query(Unit).filter(Unit.id.in_(accessible_units)).all()
    
    # Count managed units
    managed_count = len(get_managed_units(db, user.id)) if not user.is_superuser else len(units)
    
    # Group by status
    status_counts = {}
    country_counts = {}
    
    for unit in units:
        # Status grouping
        status = unit.status
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Country grouping
        country = unit.country or "Unknown"
        country_counts[country] = country_counts.get(country, 0) + 1
    
    return {
        "total_units": len(units),
        "active_units": len([u for u in units if u.is_active and u.status == "active"]),
        "managed_units": managed_count,
        "units_by_status": status_counts,
        "units_by_country": country_counts
    }


def ensure_unit_access_middleware(db: Session, user: User, requested_unit_ids: List[UUID]) -> List[UUID]:
    """
    Middleware function to ensure user only accesses authorized units.
    Filters requested unit IDs to only include accessible ones.
    
    Args:
        db: Database session
        user: User object
        requested_unit_ids: List of requested unit IDs
        
    Returns:
        Filtered list of accessible unit IDs
    """
    if user.is_superuser:
        return requested_unit_ids
    
    accessible_units = get_user_units(db, user.id)
    
    # Return intersection of requested and accessible units
    return [unit_id for unit_id in requested_unit_ids if unit_id in accessible_units]


def log_unit_access_event(
    db: Session,
    user_id: UUID,
    unit_id: UUID,
    action: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log unit access events for audit purposes.
    
    Args:
        db: Database session
        user_id: User UUID
        unit_id: Unit UUID
        action: Action performed
        details: Additional details to log
    """
    try:
        # This would integrate with UserActivity model for logging
        from app.models.user import UserActivity
        
        activity = UserActivity(
            user_id=user_id,
            activity_type="unit_access",
            description=f"Unit access: {action}",
            unit_id=unit_id,
            metadata=details or {},
            created_at=datetime.utcnow()
        )
        
        db.add(activity)
        db.commit()
        
    except Exception:
        # Don't fail the main operation if logging fails
        db.rollback()
        pass