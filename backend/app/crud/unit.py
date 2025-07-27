from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, or_, func, text, extract
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.crud.base import CRUDBase
from app.models.unit import (
    Unit, 
    UnitConfig, 
    UnitBudget
)
from app.models.user import User, UserUnitAssignment
from app.schemas.unit import (
    UnitCreate, 
    UnitUpdate,
    UnitConfigUpdate,
    UnitConfigResponse,
    UnitBudgetUpdate,
    UnitBudgetResponse,
    UnitUserResponse,
    UnitStatsResponse
)


class CRUDUnit(CRUDBase[Unit, UnitCreate, UnitUpdate]):
    def get_by_code(self, db: Session, *, unit_code: str) -> Optional[Unit]:
        """Get unit by unique code."""
        return self.get_by_field(db, field="unit_code", value=unit_code)

    def get_by_name(self, db: Session, *, name: str) -> Optional[Unit]:
        """Get unit by name."""
        return self.get_by_field(db, field="name", value=name)

    def get_multi_with_filters(
        self,
        db: Session,
        *,
        include_inactive: bool = False,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Unit], int]:
        """
        Get units with filtering options.
        """
        query = db.query(Unit).options(
            joinedload(Unit.config),
            joinedload(Unit.user_assignments)
        )
        
        # Apply soft delete filter
        if hasattr(Unit, 'is_deleted'):
            query = query.filter(Unit.is_deleted == False)
        
        # Filter by active status
        if not include_inactive:
            query = query.filter(Unit.is_active == True)
        
        # Filter by location
        if location:
            query = query.filter(
                func.lower(Unit.location).contains(location.lower())
            )
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(Unit.name.asc())
        units = query.offset(skip).limit(limit).all()
        
        return units, total

    def get_multi_by_ids(
        self,
        db: Session,
        *,
        unit_ids: List[UUID],
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Unit], int]:
        """
        Get multiple units by IDs (for user's accessible units).
        """
        query = db.query(Unit).filter(Unit.id.in_(unit_ids))
        
        # Apply soft delete filter
        if hasattr(Unit, 'is_deleted'):
            query = query.filter(Unit.is_deleted == False)
        
        # Filter by active status
        if not include_inactive:
            query = query.filter(Unit.is_active == True)
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(Unit.name.asc())
        units = query.offset(skip).limit(limit).all()
        
        return units, total

    def has_active_dependencies(self, db: Session, *, unit_id: UUID) -> bool:
        """
        Check if unit has active dependencies (products, orders, users).
        """
        # Check for active user assignments
        user_count = db.query(UserUnitAssignment).filter(
            and_(
                UserUnitAssignment.unit_id == unit_id,
                UserUnitAssignment.is_active == True
            )
        ).count()
        
        if user_count > 0:
            return True
        
        # Check for active products (would need ProductUnitAllocation model)
        # This is a placeholder - implement based on your product models
        try:
            from app.models.product import ProductUnitAllocation
            product_count = db.query(ProductUnitAllocation).filter(
                ProductUnitAllocation.unit_id == unit_id
            ).count()
            if product_count > 0:
                return True
        except ImportError:
            pass  # Product models not available yet
        
        # Check for active orders (would need Order model)
        # This is a placeholder for future implementation
        
        return False

    # Unit Configuration Management
    def get_config(self, db: Session, *, unit_id: UUID) -> Optional[UnitConfig]:
        """Get unit configuration."""
        return db.query(UnitConfig).filter(UnitConfig.unit_id == unit_id).first()

    def create_config(
        self, 
        db: Session, 
        *, 
        unit_id: UUID, 
        config_data: Dict[str, Any]
    ) -> UnitConfig:
        """Create unit configuration."""
        db_config = UnitConfig(
            unit_id=unit_id,
            **config_data
        )
        db.add(db_config)
        
        try:
            db.commit()
            db.refresh(db_config)
            return db_config
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_config(
        self,
        db: Session,
        *,
        unit_id: UUID,
        obj_in: UnitConfigUpdate
    ) -> UnitConfig:
        """Update or create unit configuration."""
        config = self.get_config(db, unit_id=unit_id)
        
        if config:
            # Update existing config
            update_data = obj_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
            config.updated_at = datetime.utcnow()
            db.add(config)
        else:
            # Create new config
            config_data = obj_in.dict(exclude_unset=True)
            config = self.create_config(db, unit_id=unit_id, config_data=config_data)
        
        try:
            db.commit()
            db.refresh(config)
            return config
        except IntegrityError as e:
            db.rollback()
            raise e

    # Unit Budget Management
    def get_budget(
        self, 
        db: Session, 
        *, 
        unit_id: UUID, 
        year: Optional[int] = None
    ) -> Optional[UnitBudget]:
        """Get unit budget for specified year (current year if not specified)."""
        if year is None:
            year = datetime.utcnow().year
        
        return db.query(UnitBudget).filter(
            and_(
                UnitBudget.unit_id == unit_id,
                UnitBudget.budget_year == year
            )
        ).first()

    def update_budget(
        self,
        db: Session,
        *,
        unit_id: UUID,
        obj_in: UnitBudgetUpdate
    ) -> UnitBudget:
        """Update or create unit budget."""
        year = obj_in.budget_year or datetime.utcnow().year
        budget = self.get_budget(db, unit_id=unit_id, year=year)
        
        if budget:
            # Update existing budget
            update_data = obj_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(budget, field, value)
            budget.updated_at = datetime.utcnow()
            db.add(budget)
        else:
            # Create new budget
            budget_data = obj_in.dict(exclude_unset=True)
            budget_data['unit_id'] = unit_id
            budget_data['budget_year'] = year
            budget = UnitBudget(**budget_data)
            db.add(budget)
        
        try:
            db.commit()
            db.refresh(budget)
            return budget
        except IntegrityError as e:
            db.rollback()
            raise e

    def get_budget_status(self, db: Session, *, unit_id: UUID) -> Dict[str, Any]:
        """Get current budget status and spending."""
        current_year = datetime.utcnow().year
        budget = self.get_budget(db, unit_id=unit_id, year=current_year)
        
        if not budget:
            return {
                "budget_year": current_year,
                "total_budget": 0,
                "spent_amount": 0,
                "remaining_amount": 0,
                "percentage_used": 0,
                "status": "no_budget_set"
            }
        
        # Calculate actual spending (this would integrate with order/purchase data)
        # Placeholder calculation - implement based on your order models
        spent_amount = Decimal('0.00')  # Would calculate from actual orders
        
        remaining_amount = budget.total_budget - spent_amount
        percentage_used = (spent_amount / budget.total_budget * 100) if budget.total_budget > 0 else 0
        
        # Determine status
        status = "on_track"
        if percentage_used >= 90:
            status = "over_budget" if percentage_used > 100 else "near_limit"
        elif percentage_used >= 75:
            status = "warning"
        
        return {
            "budget_year": current_year,
            "total_budget": float(budget.total_budget),
            "spent_amount": float(spent_amount),
            "remaining_amount": float(remaining_amount),
            "percentage_used": float(percentage_used),
            "status": status,
            "category_budgets": budget.category_budgets or {}
        }

    # User-Unit Assignment Management
    def get_unit_users(
        self,
        db: Session,
        *,
        unit_id: UUID,
        role: Optional[str] = None,
        is_active: bool = True
    ) -> List[UnitUserResponse]:
        """Get users assigned to unit."""
        query = db.query(UserUnitAssignment).join(User).filter(
            UserUnitAssignment.unit_id == unit_id
        )
        
        if role:
            query = query.filter(UserUnitAssignment.role == role)
        
        if is_active:
            query = query.filter(
                and_(
                    UserUnitAssignment.is_active == True,
                    User.is_active == True
                )
            )
        
        assignments = query.all()
        
        # Convert to response format
        user_responses = []
        for assignment in assignments:
            user_responses.append(UnitUserResponse(
                user_id=assignment.user_id,
                user=assignment.user,
                role=assignment.role,
                assigned_at=assignment.assigned_at,
                is_active=assignment.is_active
            ))
        
        return user_responses

    def get_user_unit_assignment(
        self,
        db: Session,
        *,
        user_id: UUID,
        unit_id: UUID
    ) -> Optional[UserUnitAssignment]:
        """Get specific user-unit assignment."""
        return db.query(UserUnitAssignment).filter(
            and_(
                UserUnitAssignment.user_id == user_id,
                UserUnitAssignment.unit_id == unit_id
            )
        ).first()

    def assign_user_to_unit(
        self,
        db: Session,
        *,
        user_id: UUID,
        unit_id: UUID,
        role: str
    ) -> UserUnitAssignment:
        """Assign user to unit with role."""
        assignment = UserUnitAssignment(
            user_id=user_id,
            unit_id=unit_id,
            role=role,
            assigned_at=datetime.utcnow(),
            is_active=True
        )
        db.add(assignment)
        
        try:
            db.commit()
            db.refresh(assignment)
            return assignment
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_user_unit_assignment(
        self,
        db: Session,
        *,
        user_id: UUID,
        unit_id: UUID,
        role: str
    ) -> Optional[UserUnitAssignment]:
        """Update user's role in unit."""
        assignment = self.get_user_unit_assignment(db, user_id=user_id, unit_id=unit_id)
        
        if assignment:
            assignment.role = role
            assignment.updated_at = datetime.utcnow()
            db.add(assignment)
            
            try:
                db.commit()
                db.refresh(assignment)
                return assignment
            except IntegrityError as e:
                db.rollback()
                raise e
        
        return None

    def remove_user_from_unit(
        self,
        db: Session,
        *,
        user_id: UUID,
        unit_id: UUID
    ) -> bool:
        """Remove user from unit (soft delete)."""
        assignment = self.get_user_unit_assignment(db, user_id=user_id, unit_id=unit_id)
        
        if assignment:
            assignment.is_active = False
            assignment.removed_at = datetime.utcnow()
            db.add(assignment)
            
            try:
                db.commit()
                return True
            except IntegrityError as e:
                db.rollback()
                raise e
        
        return False

    def count_unit_managers(self, db: Session, *, unit_id: UUID) -> int:
        """Count active managers for a unit."""
        return db.query(UserUnitAssignment).filter(
            and_(
                UserUnitAssignment.unit_id == unit_id,
                UserUnitAssignment.role.in_(["unit_manager", "store_manager"]),
                UserUnitAssignment.is_active == True
            )
        ).count()

    # Statistics and Dashboard Data
    def get_unit_statistics(
        self,
        db: Session,
        *,
        unit_id: UUID,
        period: str = "month"
    ) -> UnitStatsResponse:
        """Get unit statistics for dashboard."""
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Default to month
        
        # Initialize stats structure
        stats = {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_orders": 0,
            "total_spending": 0.0,
            "active_products": 0,
            "low_stock_items": 0,
            "pending_orders": 0,
            "supplier_count": 0,
            "average_order_value": 0.0,
            "order_fulfillment_rate": 0.0
        }
        
        # Get basic unit info
        try:
            # Count active products for this unit
            from app.models.product import ProductUnitAllocation
            stats["active_products"] = db.query(ProductUnitAllocation).filter(
                ProductUnitAllocation.unit_id == unit_id
            ).count()
            
            # Count low stock items
            stats["low_stock_items"] = db.query(ProductUnitAllocation).filter(
                and_(
                    ProductUnitAllocation.unit_id == unit_id,
                    ProductUnitAllocation.current_stock <= ProductUnitAllocation.reorder_point
                )
            ).count()
            
        except ImportError:
            # Product models not available yet
            pass
        
        # Count active suppliers (placeholder - implement based on supplier models)
        stats["supplier_count"] = 0  # Would calculate from supplier relationships
        
        # Additional statistics would be calculated from order data
        # This is a placeholder for future implementation
        
        return UnitStatsResponse(**stats)

    def get_recent_orders(
        self,
        db: Session,
        *,
        unit_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent orders for unit dashboard."""
        # Placeholder for order model integration
        # This would query actual order data
        return []

    def get_low_stock_alerts(
        self,
        db: Session,
        *,
        unit_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get low stock alerts for unit."""
        alerts = []
        
        try:
            from app.models.product import ProductUnitAllocation, Product
            low_stock_items = db.query(ProductUnitAllocation, Product).join(
                Product, ProductUnitAllocation.product_id == Product.id
            ).filter(
                and_(
                    ProductUnitAllocation.unit_id == unit_id,
                    ProductUnitAllocation.current_stock <= ProductUnitAllocation.reorder_point,
                    Product.is_active == True
                )
            ).all()
            
            for allocation, product in low_stock_items:
                alerts.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_stock": allocation.current_stock,
                    "reorder_point": allocation.reorder_point,
                    "recommended_order": allocation.max_stock_level - allocation.current_stock
                })
                
        except ImportError:
            # Product models not available yet
            pass
        
        return alerts

    def get_pending_approvals(
        self,
        db: Session,
        *,
        unit_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get pending approvals for unit."""
        # Placeholder for approval workflow integration
        return []

    def get_supplier_performance_summary(
        self,
        db: Session,
        *,
        unit_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get supplier performance summary for unit."""
        # Placeholder for supplier performance tracking
        return []

    def get_performance_report(
        self,
        db: Session,
        *,
        unit_id: UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get detailed performance report for unit."""
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=30)
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        
        report = {
            "unit_id": unit_id,
            "period": {
                "start_date": start_dt,
                "end_date": end_dt
            },
            "metrics": {}
        }
        
        # Default metrics if none specified
        if metrics is None:
            metrics = ["orders", "spending", "inventory", "suppliers"]
        
        # Calculate requested metrics
        for metric in metrics:
            if metric == "orders":
                report["metrics"]["orders"] = self._calculate_order_metrics(
                    db, unit_id, start_dt, end_dt
                )
            elif metric == "spending":
                report["metrics"]["spending"] = self._calculate_spending_metrics(
                    db, unit_id, start_dt, end_dt
                )
            elif metric == "inventory":
                report["metrics"]["inventory"] = self._calculate_inventory_metrics(
                    db, unit_id
                )
            elif metric == "suppliers":
                report["metrics"]["suppliers"] = self._calculate_supplier_metrics(
                    db, unit_id, start_dt, end_dt
                )
        
        return report

    def _calculate_order_metrics(
        self,
        db: Session,
        unit_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate order-related metrics."""
        # Placeholder for order metrics calculation
        return {
            "total_orders": 0,
            "completed_orders": 0,
            "pending_orders": 0,
            "cancelled_orders": 0,
            "average_processing_time": 0.0
        }

    def _calculate_spending_metrics(
        self,
        db: Session,
        unit_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate spending-related metrics."""
        # Placeholder for spending metrics calculation
        return {
            "total_spending": 0.0,
            "budget_utilization": 0.0,
            "average_order_value": 0.0,
            "category_breakdown": {}
        }

    def _calculate_inventory_metrics(
        self,
        db: Session,
        unit_id: UUID
    ) -> Dict[str, Any]:
        """Calculate inventory-related metrics."""
        try:
            from app.models.product import ProductUnitAllocation
            
            total_products = db.query(ProductUnitAllocation).filter(
                ProductUnitAllocation.unit_id == unit_id
            ).count()
            
            low_stock_count = db.query(ProductUnitAllocation).filter(
                and_(
                    ProductUnitAllocation.unit_id == unit_id,
                    ProductUnitAllocation.current_stock <= ProductUnitAllocation.reorder_point
                )
            ).count()
            
            return {
                "total_products": total_products,
                "low_stock_items": low_stock_count,
                "stock_turnover_rate": 0.0,  # Would calculate based on historical data
                "inventory_value": 0.0  # Would calculate based on product prices
            }
            
        except ImportError:
            return {
                "total_products": 0,
                "low_stock_items": 0,
                "stock_turnover_rate": 0.0,
                "inventory_value": 0.0
            }

    def _calculate_supplier_metrics(
        self,
        db: Session,
        unit_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate supplier-related metrics."""
        # Placeholder for supplier metrics calculation
        return {
            "active_suppliers": 0,
            "on_time_delivery_rate": 0.0,
            "quality_score": 0.0,
            "cost_savings": 0.0
        }


# Create the CRUD instance
crud_unit = CRUDUnit(Unit)