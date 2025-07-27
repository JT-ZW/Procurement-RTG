"""
Multi-tenant utilities for the procurement system.
Handles access control, data isolation, and unit-based permissions across 8 hotel units.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
# Temporarily simplify to avoid unit assignment complexity
# from app.models.unit import Unit


async def get_user_units(db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
    """
    Get list of units that a user has access to.
    For now, return a simplified structure since unit assignments may not be set up yet.
    
    Args:
        db: Database session
        user_id: User's UUID
        
    Returns:
        List of unit dictionaries the user can access
    """
    # Get user to check if superuser
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return []
    
    # For now, return a basic unit structure
    # This will be expanded when units table is properly set up
    if user.is_superuser:
        # Superusers get access to all 8 hotel units
        return [
            {"id": f"hotel-{i}", "name": f"Hotel Unit {i}", "code": f"HOTEL{i:03d}"}
            for i in range(1, 9)
        ]
    else:
        # Regular users get access to default unit
        return [
            {"id": "hotel-1", "name": "Hotel Unit 1", "code": "HOTEL001"}
        ]


def get_current_unit_context(user: User) -> Optional[str]:
    """
    Get current unit context for a user.
    For now, return a simple default.
    
    Args:
        user: User object
        
    Returns:
        Unit ID string or None
    """
    # For now, just return default unit
    return "hotel-1"


async def check_unit_access(db: AsyncSession, user_id: UUID, unit_id: str) -> bool:
    """
    Check if user has access to a specific unit.
    
    Args:
        db: Database session
        user_id: User's UUID
        unit_id: Unit ID to check access for
        
    Returns:
        True if user has access, False otherwise
    """
    user_units = await get_user_units(db, user_id)
    unit_ids = [unit["id"] for unit in user_units]
    return unit_id in unit_ids


def filter_by_unit_access(query, user_units: List[str], unit_field):
    """
    Filter query by units the user has access to.
    
    Args:
        query: SQLAlchemy query
        user_units: List of unit IDs user has access to
        unit_field: Database field representing unit_id
        
    Returns:
        Filtered query
    """
    if not user_units:
        # No units = no access
        return query.where(False)
    
    return query.where(unit_field.in_(user_units))
