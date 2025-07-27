"""
CRUD operations for Supplier model
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.crud.base import CRUDBase
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class CRUDSupplier(CRUDBase[Supplier, SupplierCreate, SupplierUpdate]):
    """CRUD operations for Supplier"""
    
    def get_by_code(self, db: Session, *, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by supplier code"""
        return db.query(Supplier).filter(
            and_(
                Supplier.supplier_code == supplier_code,
                Supplier.is_deleted == False
            )
        ).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[Supplier]:
        """Get supplier by email"""
        return db.query(Supplier).filter(
            and_(
                Supplier.email == email,
                Supplier.is_deleted == False
            )
        ).first()
    
    def get_by_unit(
        self, 
        db: Session, 
        *, 
        unit_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Supplier]:
        """Get suppliers by unit with optional filtering"""
        query = db.query(Supplier).filter(
            and_(
                Supplier.unit_id == unit_id,
                Supplier.is_deleted == False
            )
        )
        
        # Add search filter
        if search:
            search_filter = or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.supplier_code.ilike(f"%{search}%"),
                Supplier.email.ilike(f"%{search}%"),
                Supplier.contact_person.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Add status filter
        if status:
            query = query.filter(Supplier.status == status)
        
        return query.order_by(Supplier.name).offset(skip).limit(limit).all()
    
    def get_active_suppliers(
        self, 
        db: Session, 
        *, 
        unit_id: Optional[UUID] = None
    ) -> List[Supplier]:
        """Get all active suppliers, optionally filtered by unit"""
        query = db.query(Supplier).filter(
            and_(
                Supplier.status == "active",
                Supplier.is_deleted == False
            )
        )
        
        if unit_id:
            query = query.filter(Supplier.unit_id == unit_id)
        
        return query.order_by(Supplier.name).all()
    
    def create_with_unit(
        self, 
        db: Session, 
        *, 
        obj_in: SupplierCreate, 
        unit_id: UUID,
        created_by: UUID
    ) -> Supplier:
        """Create supplier with unit association"""
        db_obj = Supplier(
            **obj_in.model_dump(),
            unit_id=unit_id,
            created_by=created_by,
            updated_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_with_user(
        self,
        db: Session,
        *,
        db_obj: Supplier,
        obj_in: Union[SupplierUpdate, Dict[str, Any]],
        updated_by: UUID
    ) -> Supplier:
        """Update supplier with user tracking"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        update_data["updated_by"] = updated_by
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def soft_delete(
        self, 
        db: Session, 
        *, 
        id: UUID, 
        deleted_by: UUID
    ) -> Optional[Supplier]:
        """Soft delete supplier"""
        db_obj = self.get(db, id=id)
        if db_obj:
            update_data = {
                "is_deleted": True,
                "deleted_at": func.now(),
                "deleted_by": deleted_by,
                "status": "inactive"
            }
            return self.update(db, db_obj=db_obj, obj_in=update_data)
        return None
    
    def get_supplier_stats(
        self, 
        db: Session, 
        *, 
        unit_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get supplier statistics"""
        query = db.query(Supplier).filter(Supplier.is_deleted == False)
        
        if unit_id:
            query = query.filter(Supplier.unit_id == unit_id)
        
        total_suppliers = query.count()
        active_suppliers = query.filter(Supplier.status == "active").count()
        inactive_suppliers = query.filter(Supplier.status == "inactive").count()
        pending_suppliers = query.filter(Supplier.status == "pending").count()
        
        return {
            "total_suppliers": total_suppliers,
            "active_suppliers": active_suppliers,
            "inactive_suppliers": inactive_suppliers,
            "pending_suppliers": pending_suppliers
        }


# Create instance
crud_supplier = CRUDSupplier(Supplier)
