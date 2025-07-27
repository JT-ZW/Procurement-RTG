"""
Purchase Requisition API Endpoints
Handles CRUD operations and workflow management for purchase requisitions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date

from app.api.deps import get_db, get_current_user, get_current_active_user
from app.core.exceptions import (
    NotFoundException as NotFound, 
    ValidationException as UnprocessableEntity,
    AuthorizationException as Forbidden, 
    TenantException as BadRequest
)
from app.models.user import User
from app.models.purchase_requisition import (
    PurchaseRequisition, RequisitionItem, RequisitionApproval, 
    RequisitionComment, RequisitionStatus, RequisitionPriority
)
from app.schemas.requisition import (
    RequisitionCreate, RequisitionUpdate, RequisitionResponse,
    RequisitionItemCreate, RequisitionItemUpdate, RequisitionItemResponse,
    RequisitionApprovalCreate, RequisitionApprovalResponse,
    RequisitionCommentCreate, RequisitionCommentResponse,
    RequisitionListResponse, RequisitionStatusUpdate
)
from app.crud.requisition import requisition_crud
from app.utils.multi_tenant import check_unit_access, get_user_accessible_units

router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=RequisitionResponse, status_code=status.HTTP_201_CREATED)
async def create_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_in: RequisitionCreate
) -> RequisitionResponse:
    """
    Create a new purchase requisition.
    Requires appropriate permissions for the target unit.
    """
    # Check unit access
    if not check_unit_access(current_user, requisition_in.unit_id):
        raise Forbidden("You don't have access to create requisitions for this unit")
    
    # Validate required by date is in the future
    if requisition_in.required_by_date <= datetime.now():
        raise BadRequest("Required by date must be in the future")
    
    # Create requisition with auto-generated number
    requisition_data = requisition_in.dict()
    requisition_data.update({
        "requested_by": current_user.id,
        "created_by": current_user.id,
        "requisition_number": await _generate_requisition_number(db, requisition_in.unit_id)
    })
    
    requisition = await requisition_crud.create(db, obj_in=requisition_data)
    return RequisitionResponse.from_orm(requisition)


@router.get("/", response_model=RequisitionListResponse)
async def list_requisitions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    unit_id: Optional[str] = Query(None, description="Filter by unit ID"),
    status: Optional[RequisitionStatus] = Query(None, description="Filter by status"),
    priority: Optional[RequisitionPriority] = Query(None, description="Filter by priority"),
    requested_by: Optional[str] = Query(None, description="Filter by requestor"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in title, description, or requisition number")
) -> RequisitionListResponse:
    """
    List purchase requisitions with filtering and pagination.
    Users can only see requisitions from units they have access to.
    """
    # Get user's accessible units
    accessible_units = get_user_accessible_units(current_user)
    
    # Build query filters
    filters = [PurchaseRequisition.is_deleted == False]
    
    # Unit access filter
    if unit_id:
        if unit_id not in [str(u) for u in accessible_units]:
            raise Forbidden("You don't have access to this unit")
        filters.append(PurchaseRequisition.unit_id == unit_id)
    else:
        filters.append(PurchaseRequisition.unit_id.in_(accessible_units))
    
    # Status filter
    if status:
        filters.append(PurchaseRequisition.status == status)
    
    # Priority filter
    if priority:
        filters.append(PurchaseRequisition.priority == priority)
    
    # Requestor filter
    if requested_by:
        filters.append(PurchaseRequisition.requested_by == requested_by)
    
    # Date range filter
    if date_from:
        filters.append(PurchaseRequisition.requested_date >= date_from)
    if date_to:
        filters.append(PurchaseRequisition.requested_date <= date_to)
    
    # Search filter
    if search:
        search_filter = or_(
            PurchaseRequisition.title.ilike(f"%{search}%"),
            PurchaseRequisition.description.ilike(f"%{search}%"),
            PurchaseRequisition.requisition_number.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    # Execute query with pagination
    query = db.query(PurchaseRequisition).filter(and_(*filters))
    total = query.count()
    
    requisitions = query.order_by(
        PurchaseRequisition.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return RequisitionListResponse(
        items=[RequisitionResponse.from_orm(req) for req in requisitions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{requisition_id}", response_model=RequisitionResponse)
async def get_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str
) -> RequisitionResponse:
    """
    Get a specific purchase requisition by ID.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check unit access
    if not check_unit_access(current_user, requisition.unit_id):
        raise Forbidden("You don't have access to this requisition")
    
    return RequisitionResponse.from_orm(requisition)


@router.put("/{requisition_id}", response_model=RequisitionResponse)
async def update_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    requisition_in: RequisitionUpdate
) -> RequisitionResponse:
    """
    Update a purchase requisition.
    Only draft requisitions can be fully updated.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check unit access
    if not check_unit_access(current_user, requisition.unit_id):
        raise Forbidden("You don't have access to this requisition")
    
    # Check if requisition can be updated
    if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.SUBMITTED]:
        raise BadRequest("Only draft or submitted requisitions can be updated")
    
    # Validate ownership or appropriate permissions
    if (requisition.requested_by != current_user.id and 
        not _can_manage_requisition(current_user, requisition)):
        raise Forbidden("You can only update your own requisitions")
    
    # Update requisition
    update_data = requisition_in.dict(exclude_unset=True)
    update_data["updated_by"] = current_user.id
    
    requisition = await requisition_crud.update(db, db_obj=requisition, obj_in=update_data)
    return RequisitionResponse.from_orm(requisition)


@router.post("/{requisition_id}/submit")
async def submit_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str
) -> RequisitionResponse:
    """
    Submit a requisition for approval.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check ownership or permissions
    if (requisition.requested_by != current_user.id and 
        not _can_manage_requisition(current_user, requisition)):
        raise Forbidden("You can only submit your own requisitions")
    
    # Validate requisition can be submitted
    if requisition.status != RequisitionStatus.DRAFT:
        raise BadRequest("Only draft requisitions can be submitted")
    
    # Validate requisition has items
    if not requisition.items:
        raise BadRequest("Requisition must have at least one item to be submitted")
    
    # Update status and timestamps
    update_data = {
        "status": RequisitionStatus.SUBMITTED,
        "submitted_at": datetime.now(),
        "updated_by": current_user.id
    }
    
    # Determine next approver based on value and approval rules
    next_approver = await _determine_next_approver(db, requisition)
    if next_approver:
        update_data["current_approver_id"] = next_approver.id
        update_data["status"] = RequisitionStatus.PENDING_APPROVAL
    
    requisition = await requisition_crud.update(db, db_obj=requisition, obj_in=update_data)
    
    # Create system comment
    await _create_system_comment(
        db, requisition.id, 
        f"Requisition submitted for approval by {current_user.full_name}",
        current_user.id
    )
    
    # TODO: Send notification to approver
    
    return RequisitionResponse.from_orm(requisition)


@router.post("/{requisition_id}/approve")
async def approve_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    approval_in: RequisitionApprovalCreate
) -> RequisitionResponse:
    """
    Approve a purchase requisition.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check if user can approve this requisition
    if not _can_approve_requisition(current_user, requisition):
        raise Forbidden("You don't have permission to approve this requisition")
    
    # Validate requisition status
    if requisition.status != RequisitionStatus.PENDING_APPROVAL:
        raise BadRequest("Only pending requisitions can be approved")
    
    # Create approval record
    approval_data = approval_in.dict()
    approval_data.update({
        "requisition_id": requisition_id,
        "approver_id": current_user.id,
        "approver_role": current_user.role,
        "approval_level": requisition.approval_level,
        "decision": "approved"
    })
    
    approval = RequisitionApproval(**approval_data)
    db.add(approval)
    
    # Update requisition status
    update_data = {"updated_by": current_user.id}
    
    # Check if more approvals needed
    if requisition.approval_level >= requisition.requires_approval_levels:
        update_data.update({
            "status": RequisitionStatus.APPROVED,
            "approved_at": datetime.now(),
            "current_approver_id": None
        })
    else:
        # Move to next approval level
        next_approver = await _determine_next_approver(db, requisition, requisition.approval_level + 1)
        update_data.update({
            "approval_level": requisition.approval_level + 1,
            "current_approver_id": next_approver.id if next_approver else None
        })
    
    requisition = await requisition_crud.update(db, db_obj=requisition, obj_in=update_data)
    
    # Create system comment
    await _create_system_comment(
        db, requisition.id,
        f"Requisition approved at level {approval.approval_level} by {current_user.full_name}",
        current_user.id
    )
    
    db.commit()
    return RequisitionResponse.from_orm(requisition)


@router.post("/{requisition_id}/reject")
async def reject_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    approval_in: RequisitionApprovalCreate
) -> RequisitionResponse:
    """
    Reject a purchase requisition.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check if user can approve/reject this requisition
    if not _can_approve_requisition(current_user, requisition):
        raise Forbidden("You don't have permission to reject this requisition")
    
    # Validate requisition status
    if requisition.status != RequisitionStatus.PENDING_APPROVAL:
        raise BadRequest("Only pending requisitions can be rejected")
    
    # Create rejection record
    approval_data = approval_in.dict()
    approval_data.update({
        "requisition_id": requisition_id,
        "approver_id": current_user.id,
        "approver_role": current_user.role,
        "approval_level": requisition.approval_level,
        "decision": "rejected"
    })
    
    approval = RequisitionApproval(**approval_data)
    db.add(approval)
    
    # Update requisition status
    update_data = {
        "status": RequisitionStatus.REJECTED,
        "rejected_at": datetime.now(),
        "rejected_by": current_user.id,
        "rejection_reason": approval_in.comments,
        "current_approver_id": None,
        "updated_by": current_user.id
    }
    
    requisition = await requisition_crud.update(db, db_obj=requisition, obj_in=update_data)
    
    # Create system comment
    await _create_system_comment(
        db, requisition.id,
        f"Requisition rejected by {current_user.full_name}: {approval_in.comments}",
        current_user.id
    )
    
    db.commit()
    return RequisitionResponse.from_orm(requisition)


@router.delete("/{requisition_id}")
async def delete_requisition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str
):
    """
    Soft delete a purchase requisition.
    Only draft requisitions can be deleted.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check ownership or permissions
    if (requisition.requested_by != current_user.id and 
        not _can_manage_requisition(current_user, requisition)):
        raise Forbidden("You can only delete your own requisitions")
    
    # Validate requisition can be deleted
    if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.REJECTED]:
        raise BadRequest("Only draft or rejected requisitions can be deleted")
    
    # Soft delete
    update_data = {
        "is_deleted": True,
        "deleted_at": datetime.now(),
        "deleted_by": current_user.id
    }
    
    await requisition_crud.update(db, db_obj=requisition, obj_in=update_data)
    
    return {"message": "Requisition deleted successfully"}


# ========== REQUISITION ITEMS ENDPOINTS ==========

@router.post("/{requisition_id}/items", response_model=RequisitionItemResponse)
async def add_requisition_item(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    item_in: RequisitionItemCreate
) -> RequisitionItemResponse:
    """
    Add an item to a purchase requisition.
    """
    requisition = await _get_editable_requisition(db, requisition_id, current_user)
    
    # Get next line number
    max_line = db.query(func.max(RequisitionItem.line_number)).filter(
        RequisitionItem.requisition_id == requisition_id
    ).scalar() or 0
    
    # Create item
    item_data = item_in.dict()
    item_data.update({
        "requisition_id": requisition_id,
        "line_number": max_line + 1
    })
    
    item = RequisitionItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return RequisitionItemResponse.from_orm(item)


@router.put("/{requisition_id}/items/{item_id}", response_model=RequisitionItemResponse)
async def update_requisition_item(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    item_id: str,
    item_in: RequisitionItemUpdate
) -> RequisitionItemResponse:
    """
    Update a requisition item.
    """
    requisition = await _get_editable_requisition(db, requisition_id, current_user)
    
    item = db.query(RequisitionItem).filter(
        and_(
            RequisitionItem.id == item_id,
            RequisitionItem.requisition_id == requisition_id
        )
    ).first()
    
    if not item:
        raise NotFound("Requisition item not found")
    
    # Update item
    update_data = item_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    return RequisitionItemResponse.from_orm(item)


@router.delete("/{requisition_id}/items/{item_id}")
async def delete_requisition_item(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    item_id: str
):
    """
    Remove an item from a requisition.
    """
    requisition = await _get_editable_requisition(db, requisition_id, current_user)
    
    item = db.query(RequisitionItem).filter(
        and_(
            RequisitionItem.id == item_id,
            RequisitionItem.requisition_id == requisition_id
        )
    ).first()
    
    if not item:
        raise NotFound("Requisition item not found")
    
    db.delete(item)
    db.commit()
    
    return {"message": "Item removed successfully"}


# ========== COMMENTS ENDPOINTS ==========

@router.post("/{requisition_id}/comments", response_model=RequisitionCommentResponse)
async def add_comment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str,
    comment_in: RequisitionCommentCreate
) -> RequisitionCommentResponse:
    """
    Add a comment to a requisition.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check unit access
    if not check_unit_access(current_user, requisition.unit_id):
        raise Forbidden("You don't have access to this requisition")
    
    # Create comment
    comment_data = comment_in.dict()
    comment_data.update({
        "requisition_id": requisition_id,
        "author_id": current_user.id,
        "author_role": current_user.role
    })
    
    comment = RequisitionComment(**comment_data)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return RequisitionCommentResponse.from_orm(comment)


@router.get("/{requisition_id}/comments", response_model=List[RequisitionCommentResponse])
async def get_comments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    requisition_id: str
) -> List[RequisitionCommentResponse]:
    """
    Get all comments for a requisition.
    """
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check unit access
    if not check_unit_access(current_user, requisition.unit_id):
        raise Forbidden("You don't have access to this requisition")
    
    comments = db.query(RequisitionComment).filter(
        and_(
            RequisitionComment.requisition_id == requisition_id,
            RequisitionComment.is_deleted == False
        )
    ).order_by(RequisitionComment.created_at.asc()).all()
    
    return [RequisitionCommentResponse.from_orm(comment) for comment in comments]


# ========== HELPER FUNCTIONS ==========

async def _generate_requisition_number(db: Session, unit_id: str) -> str:
    """Generate a unique requisition number."""
    # Get unit code for prefix
    from app.models.unit import Unit
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    unit_code = unit.code if unit else "UNKNOWN"
    
    # Get current date
    date_str = datetime.now().strftime("%Y%m")
    
    # Get next sequence number
    prefix = f"REQ-{unit_code}-{date_str}-"
    last_req = db.query(PurchaseRequisition).filter(
        PurchaseRequisition.requisition_number.like(f"{prefix}%")
    ).order_by(PurchaseRequisition.requisition_number.desc()).first()
    
    if last_req:
        last_num = int(last_req.requisition_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


async def _determine_next_approver(db: Session, requisition: PurchaseRequisition, level: int = 1) -> Optional[User]:
    """Determine the next approver based on approval rules."""
    # TODO: Implement approval matrix logic based on:
    # - Requisition value
    # - Unit/department
    # - Approval levels configuration
    # For now, return None (manual assignment needed)
    return None


def _can_manage_requisition(user: User, requisition: PurchaseRequisition) -> bool:
    """Check if user can manage (edit/delete) the requisition."""
    # Super admins and procurement admins can manage all requisitions
    if user.role in ["super_admin", "procurement_admin"]:
        return True
    
    # Unit managers can manage requisitions in their units
    if user.role == "unit_manager" and user.unit_id == requisition.unit_id:
        return True
    
    return False


def _can_approve_requisition(user: User, requisition: PurchaseRequisition) -> bool:
    """Check if user can approve the requisition."""
    # Must be the current approver or have admin privileges
    if requisition.current_approver_id == user.id:
        return True
    
    if user.role in ["super_admin", "procurement_admin"]:
        return True
    
    # Unit managers can approve requisitions in their units
    if user.role == "unit_manager" and user.unit_id == requisition.unit_id:
        return True
    
    return False


async def _get_editable_requisition(db: Session, requisition_id: str, user: User) -> PurchaseRequisition:
    """Get a requisition that can be edited by the current user."""
    requisition = await requisition_crud.get(db, id=requisition_id)
    if not requisition:
        raise NotFound("Purchase requisition not found")
    
    # Check unit access
    if not check_unit_access(user, requisition.unit_id):
        raise Forbidden("You don't have access to this requisition")
    
    # Check if requisition can be edited
    if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.SUBMITTED]:
        raise BadRequest("Only draft or submitted requisitions can be edited")
    
    # Check ownership or permissions
    if (requisition.requested_by != user.id and not _can_manage_requisition(user, requisition)):
        raise Forbidden("You can only edit your own requisitions")
    
    return requisition


async def _create_system_comment(db: Session, requisition_id: str, message: str, user_id: str):
    """Create a system-generated comment."""
    comment = RequisitionComment(
        requisition_id=requisition_id,
        comment_text=message,
        comment_type="system",
        author_id=user_id,
        is_system_generated=True
    )
    db.add(comment)
