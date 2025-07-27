"""
Purchase Requisition CRUD Operations
Database operations for purchase requisitions, items, approvals, and comments.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, text
from datetime import datetime, timedelta
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.purchase_requisition import (
    PurchaseRequisition, RequisitionItem, RequisitionApproval, 
    RequisitionComment, RequisitionStatus, RequisitionPriority
)
from app.models.user import User
from app.models.unit import Unit
from app.models.supplier import Supplier
from app.models.product import Product
from app.schemas.requisition import (
    RequisitionCreate, RequisitionUpdate, RequisitionItemCreate,
    RequisitionItemUpdate, RequisitionStats
)


class CRUDRequisition(CRUDBase[PurchaseRequisition, RequisitionCreate, RequisitionUpdate]):
    """CRUD operations for purchase requisitions."""
    
    def get_by_number(self, db: Session, *, requisition_number: str) -> Optional[PurchaseRequisition]:
        """Get requisition by number."""
        return db.query(PurchaseRequisition).filter(
            and_(
                PurchaseRequisition.requisition_number == requisition_number,
                PurchaseRequisition.is_deleted == False
            )
        ).first()
    
    def get_with_details(self, db: Session, *, id: str) -> Optional[PurchaseRequisition]:
        """Get requisition with all related data loaded."""
        return db.query(PurchaseRequisition).options(
            joinedload(PurchaseRequisition.unit),
            joinedload(PurchaseRequisition.requestor),
            joinedload(PurchaseRequisition.current_approver),
            joinedload(PurchaseRequisition.preferred_supplier),
            joinedload(PurchaseRequisition.items).joinedload(RequisitionItem.product),
            joinedload(PurchaseRequisition.approvals).joinedload(RequisitionApproval.approver),
            joinedload(PurchaseRequisition.comments).joinedload(RequisitionComment.author)
        ).filter(
            and_(
                PurchaseRequisition.id == id,
                PurchaseRequisition.is_deleted == False
            )
        ).first()
    
    def get_multi_by_unit(
        self, 
        db: Session, 
        *, 
        unit_ids: List[str],
        status: Optional[RequisitionStatus] = None,
        priority: Optional[RequisitionPriority] = None,
        requested_by: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[PurchaseRequisition]:
        """Get requisitions for specific units with filtering."""
        query = db.query(PurchaseRequisition).options(
            joinedload(PurchaseRequisition.requestor),
            joinedload(PurchaseRequisition.unit),
            joinedload(PurchaseRequisition.current_approver)
        ).filter(
            and_(
                PurchaseRequisition.unit_id.in_(unit_ids),
                PurchaseRequisition.is_deleted == False
            )
        )
        
        # Apply filters
        if status:
            query = query.filter(PurchaseRequisition.status == status)
        
        if priority:
            query = query.filter(PurchaseRequisition.priority == priority)
        
        if requested_by:
            query = query.filter(PurchaseRequisition.requested_by == requested_by)
        
        if date_from:
            query = query.filter(PurchaseRequisition.requested_date >= date_from)
        
        if date_to:
            query = query.filter(PurchaseRequisition.requested_date <= date_to)
        
        if search:
            search_filter = or_(
                PurchaseRequisition.title.ilike(f"%{search}%"),
                PurchaseRequisition.description.ilike(f"%{search}%"),
                PurchaseRequisition.requisition_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.order_by(
            desc(PurchaseRequisition.created_at)
        ).offset(skip).limit(limit).all()
    
    def count_by_unit(
        self, 
        db: Session, 
        *, 
        unit_ids: List[str],
        status: Optional[RequisitionStatus] = None,
        priority: Optional[RequisitionPriority] = None,
        requested_by: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> int:
        """Count requisitions for specific units with filtering."""
        query = db.query(PurchaseRequisition).filter(
            and_(
                PurchaseRequisition.unit_id.in_(unit_ids),
                PurchaseRequisition.is_deleted == False
            )
        )
        
        # Apply same filters as get_multi_by_unit
        if status:
            query = query.filter(PurchaseRequisition.status == status)
        if priority:
            query = query.filter(PurchaseRequisition.priority == priority)
        if requested_by:
            query = query.filter(PurchaseRequisition.requested_by == requested_by)
        if date_from:
            query = query.filter(PurchaseRequisition.requested_date >= date_from)
        if date_to:
            query = query.filter(PurchaseRequisition.requested_date <= date_to)
        if search:
            search_filter = or_(
                PurchaseRequisition.title.ilike(f"%{search}%"),
                PurchaseRequisition.description.ilike(f"%{search}%"),
                PurchaseRequisition.requisition_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.count()
    
    def get_pending_approvals(
        self, 
        db: Session, 
        *, 
        approver_id: str,
        unit_ids: Optional[List[str]] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[PurchaseRequisition]:
        """Get requisitions pending approval by a specific user."""
        query = db.query(PurchaseRequisition).options(
            joinedload(PurchaseRequisition.requestor),
            joinedload(PurchaseRequisition.unit)
        ).filter(
            and_(
                PurchaseRequisition.status == RequisitionStatus.PENDING_APPROVAL,
                PurchaseRequisition.current_approver_id == approver_id,
                PurchaseRequisition.is_deleted == False
            )
        )
        
        if unit_ids:
            query = query.filter(PurchaseRequisition.unit_id.in_(unit_ids))
        
        return query.order_by(
            PurchaseRequisition.priority.desc(),
            PurchaseRequisition.required_by_date.asc()
        ).offset(skip).limit(limit).all()
    
    def get_urgent_requisitions(
        self, 
        db: Session, 
        *, 
        unit_ids: List[str],
        days_threshold: int = 3,
        skip: int = 0, 
        limit: int = 100
    ) -> List[PurchaseRequisition]:
        """Get urgent requisitions (high priority or due soon)."""
        cutoff_date = datetime.now() + timedelta(days=days_threshold)
        
        query = db.query(PurchaseRequisition).options(
            joinedload(PurchaseRequisition.requestor),
            joinedload(PurchaseRequisition.unit)
        ).filter(
            and_(
                PurchaseRequisition.unit_id.in_(unit_ids),
                PurchaseRequisition.status.in_([
                    RequisitionStatus.SUBMITTED,
                    RequisitionStatus.PENDING_APPROVAL,
                    RequisitionStatus.APPROVED
                ]),
                or_(
                    PurchaseRequisition.priority.in_([
                        RequisitionPriority.HIGH,
                        RequisitionPriority.URGENT,
                        RequisitionPriority.EMERGENCY
                    ]),
                    PurchaseRequisition.required_by_date <= cutoff_date
                ),
                PurchaseRequisition.is_deleted == False
            )
        )
        
        return query.order_by(
            PurchaseRequisition.priority.desc(),
            PurchaseRequisition.required_by_date.asc()
        ).offset(skip).limit(limit).all()
    
    def get_stats(
        self, 
        db: Session, 
        *, 
        unit_ids: List[str],
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> RequisitionStats:
        """Get requisition statistics for units."""
        base_query = db.query(PurchaseRequisition).filter(
            and_(
                PurchaseRequisition.unit_id.in_(unit_ids),
                PurchaseRequisition.is_deleted == False
            )
        )
        
        # Apply date filter if provided
        if date_from:
            base_query = base_query.filter(PurchaseRequisition.requested_date >= date_from)
        if date_to:
            base_query = base_query.filter(PurchaseRequisition.requested_date <= date_to)
        
        # Get total count
        total_requisitions = base_query.count()
        
        # Get count by status
        status_counts = {}
        for status in RequisitionStatus:
            count = base_query.filter(PurchaseRequisition.status == status).count()
            status_counts[status.value + "_count"] = count
        
        # Get total value
        total_value_result = base_query.with_entities(
            func.sum(PurchaseRequisition.estimated_total_value)
        ).scalar()
        total_value = total_value_result or Decimal(0)
        
        # Calculate average approval time
        avg_approval_time = None
        approved_reqs = base_query.filter(
            and_(
                PurchaseRequisition.status == RequisitionStatus.APPROVED,
                PurchaseRequisition.submitted_at.isnot(None),
                PurchaseRequisition.approved_at.isnot(None)
            )
        )
        
        if approved_reqs.count() > 0:
            # Calculate average hours between submission and approval
            time_diffs = []
            for req in approved_reqs:
                if req.submitted_at and req.approved_at:
                    diff = req.approved_at - req.submitted_at
                    time_diffs.append(diff.total_seconds() / 3600)  # Convert to hours
            
            if time_diffs:
                avg_approval_time = sum(time_diffs) / len(time_diffs)
        
        return RequisitionStats(
            total_requisitions=total_requisitions,
            total_value=total_value,
            average_approval_time_hours=avg_approval_time,
            **status_counts
        )
    
    def create_with_number(
        self, db: Session, *, obj_in: RequisitionCreate, 
        requisition_number: str, created_by: str
    ) -> PurchaseRequisition:
        """Create requisition with auto-generated number."""
        db_obj_data = obj_in.dict()
        db_obj_data.update({
            "requisition_number": requisition_number,
            "created_by": created_by,
            "requested_by": created_by
        })
        
        db_obj = PurchaseRequisition(**db_obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def soft_delete(self, db: Session, *, id: str, deleted_by: str) -> PurchaseRequisition:
        """Soft delete a requisition."""
        db_obj = self.get(db, id=id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now()
            db_obj.deleted_by = deleted_by
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj
    
    def update_status(
        self, 
        db: Session, 
        *, 
        db_obj: PurchaseRequisition, 
        status: RequisitionStatus,
        updated_by: str,
        **kwargs
    ) -> PurchaseRequisition:
        """Update requisition status with timestamp."""
        status_timestamps = {
            RequisitionStatus.SUBMITTED: "submitted_at",
            RequisitionStatus.APPROVED: "approved_at",
            RequisitionStatus.REJECTED: "rejected_at",
            RequisitionStatus.FULFILLED: "fulfilled_at",
            RequisitionStatus.CANCELLED: "cancelled_at"
        }
        
        db_obj.status = status
        db_obj.updated_by = updated_by
        
        # Set appropriate timestamp
        if status in status_timestamps:
            setattr(db_obj, status_timestamps[status], datetime.now())
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDRequisitionItem(CRUDBase[RequisitionItem, RequisitionItemCreate, RequisitionItemUpdate]):
    """CRUD operations for requisition items."""
    
    def get_by_requisition(
        self, db: Session, *, requisition_id: str
    ) -> List[RequisitionItem]:
        """Get all items for a requisition."""
        return db.query(RequisitionItem).options(
            joinedload(RequisitionItem.product),
            joinedload(RequisitionItem.preferred_supplier)
        ).filter(
            RequisitionItem.requisition_id == requisition_id
        ).order_by(RequisitionItem.line_number).all()
    
    def create_with_line_number(
        self, db: Session, *, obj_in: RequisitionItemCreate, 
        requisition_id: str, line_number: int
    ) -> RequisitionItem:
        """Create item with specific line number."""
        db_obj_data = obj_in.dict()
        db_obj_data.update({
            "requisition_id": requisition_id,
            "line_number": line_number
        })
        
        # Calculate total price if unit price provided
        if db_obj_data.get("estimated_unit_price"):
            db_obj_data["estimated_total_price"] = (
                db_obj_data["estimated_unit_price"] * db_obj_data["quantity_requested"]
            )
        
        db_obj = RequisitionItem(**db_obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_next_line_number(self, db: Session, *, requisition_id: str) -> int:
        """Get the next available line number for a requisition."""
        max_line = db.query(func.max(RequisitionItem.line_number)).filter(
            RequisitionItem.requisition_id == requisition_id
        ).scalar()
        
        return (max_line or 0) + 1
    
    def update_quantities(
        self, db: Session, *, db_obj: RequisitionItem, 
        quantity_approved: Optional[Decimal] = None,
        quantity_fulfilled: Optional[Decimal] = None
    ) -> RequisitionItem:
        """Update item quantities."""
        if quantity_approved is not None:
            db_obj.quantity_approved = quantity_approved
            
            # Update approved total price if approved unit price exists
            if db_obj.approved_unit_price:
                db_obj.approved_total_price = db_obj.approved_unit_price * quantity_approved
        
        if quantity_fulfilled is not None:
            db_obj.quantity_fulfilled = quantity_fulfilled
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDRequisitionApproval(CRUDBase[RequisitionApproval, dict, dict]):
    """CRUD operations for requisition approvals."""
    
    def get_by_requisition(
        self, db: Session, *, requisition_id: str
    ) -> List[RequisitionApproval]:
        """Get all approvals for a requisition."""
        return db.query(RequisitionApproval).options(
            joinedload(RequisitionApproval.approver)
        ).filter(
            RequisitionApproval.requisition_id == requisition_id
        ).order_by(RequisitionApproval.approval_level, RequisitionApproval.decision_date).all()
    
    def create_approval(
        self, db: Session, *, requisition_id: str, approver_id: str,
        approval_level: int, decision: str, **kwargs
    ) -> RequisitionApproval:
        """Create an approval record."""
        db_obj = RequisitionApproval(
            requisition_id=requisition_id,
            approver_id=approver_id,
            approval_level=approval_level,
            decision=decision,
            **kwargs
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_latest_approval(
        self, db: Session, *, requisition_id: str
    ) -> Optional[RequisitionApproval]:
        """Get the most recent approval for a requisition."""
        return db.query(RequisitionApproval).filter(
            RequisitionApproval.requisition_id == requisition_id
        ).order_by(desc(RequisitionApproval.decision_date)).first()


class CRUDRequisitionComment(CRUDBase[RequisitionComment, dict, dict]):
    """CRUD operations for requisition comments."""
    
    def get_by_requisition(
        self, db: Session, *, requisition_id: str, 
        include_deleted: bool = False
    ) -> List[RequisitionComment]:
        """Get all comments for a requisition."""
        query = db.query(RequisitionComment).options(
            joinedload(RequisitionComment.author)
        ).filter(
            RequisitionComment.requisition_id == requisition_id
        )
        
        if not include_deleted:
            query = query.filter(RequisitionComment.is_deleted == False)
        
        return query.order_by(RequisitionComment.created_at).all()
    
    def create_comment(
        self, db: Session, *, requisition_id: str, author_id: str,
        comment_text: str, **kwargs
    ) -> RequisitionComment:
        """Create a comment."""
        db_obj = RequisitionComment(
            requisition_id=requisition_id,
            author_id=author_id,
            comment_text=comment_text,
            **kwargs
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def soft_delete_comment(
        self, db: Session, *, id: str, deleted_by: str
    ) -> Optional[RequisitionComment]:
        """Soft delete a comment."""
        db_obj = self.get(db, id=id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now()
            db_obj.deleted_by = deleted_by
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj
    
    def mark_resolved(
        self, db: Session, *, id: str, resolved_by: str
    ) -> Optional[RequisitionComment]:
        """Mark a comment as resolved."""
        db_obj = self.get(db, id=id)
        if db_obj:
            db_obj.is_resolved = True
            db_obj.resolved_by = resolved_by
            db_obj.resolved_at = datetime.now()
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj


# Create instances
requisition_crud = CRUDRequisition(PurchaseRequisition)
requisition_item_crud = CRUDRequisitionItem(RequisitionItem)
requisition_approval_crud = CRUDRequisitionApproval(RequisitionApproval)
requisition_comment_crud = CRUDRequisitionComment(RequisitionComment)
