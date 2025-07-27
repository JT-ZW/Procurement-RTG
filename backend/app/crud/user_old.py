from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, func, text, extract
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserActivity, UserUnitAssignment
from app.schemas.user import (
    UserCreate, 
    UserUpdate,
    UserProfileUpdate,
    UserStatsResponse,
    UserActivityResponse
)


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(
            func.lower(User.email) == email.lower()
        ).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username (if username field exists)."""
        if hasattr(User, 'username'):
            return db.query(User).filter(User.username == username).first()
        return None

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser

    def get_multi_with_filters(
        self,
        db: Session,
        *,
        unit_ids: Optional[List[UUID]] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[User], int]:
        """
        Get users with comprehensive filtering for multi-tenant support.
        """
        query = db.query(User).options(
            joinedload(User.unit_assignments)
        )
        
        # Apply soft delete filter
        if hasattr(User, 'is_deleted'):
            query = query.filter(User.is_deleted == False)
        
        # Filter by active status
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Filter by role
        if role:
            query = query.filter(User.role == role)
        
        # Filter by units (multi-tenant)
        if unit_ids:
            query = query.join(UserUnitAssignment).filter(
                and_(
                    UserUnitAssignment.unit_id.in_(unit_ids),
                    UserUnitAssignment.is_active == True
                )
            )
        
        # Search functionality
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.first_name).like(search_term),
                    func.lower(User.last_name).like(search_term),
                    func.lower(User.email).like(search_term),
                    func.concat(
                        func.lower(User.first_name), 
                        ' ', 
                        func.lower(User.last_name)
                    ).like(search_term)
                )
            )
        
        # Remove duplicates if joined with other tables
        query = query.distinct()
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(User.first_name.asc(), User.last_name.asc())
        users = query.offset(skip).limit(limit).all()
        
        return users, total

    def create(self, db: Session, *, obj_in: UserCreate, created_by: Optional[UUID] = None) -> User:
        """
        Create user with password hashing and unit assignments.
        """
        # Prepare user data
        user_data = obj_in.dict(exclude={'password', 'unit_assignments'})
        
        # Hash password
        if obj_in.password:
            user_data['hashed_password'] = get_password_hash(obj_in.password)
        
        # Add creation metadata
        if created_by:
            user_data['created_by'] = created_by
        
        # Create base user
        db_user = User(**user_data)
        db.add(db_user)
        
        try:
            db.flush()  # Get the user ID without committing
            
            # Create unit assignments if provided
            if obj_in.unit_assignments:
                for assignment in obj_in.unit_assignments:
                    db_assignment = UserUnitAssignment(
                        user_id=db_user.id,
                        unit_id=assignment.unit_id,
                        role=assignment.role,
                        assigned_at=datetime.utcnow(),
                        is_active=True
                    )
                    db.add(db_assignment)
            
            # Log user creation activity
            self._log_activity(
                db, 
                user_id=db_user.id, 
                activity_type="user_created",
                description=f"User account created with role: {db_user.role}",
                performed_by=created_by
            )
            
            db.commit()
            db.refresh(db_user)
            return db_user
            
        except IntegrityError as e:
            db.rollback()
            raise e

    def update(
        self, 
        db: Session, 
        *, 
        db_obj: User, 
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update user with password hashing if password is provided.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        # Update user fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Update timestamp
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_profile(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: UserProfileUpdate
    ) -> User:
        """
        Update user profile information (non-sensitive fields).
        """
        update_data = obj_in.dict(exclude_unset=True)
        
        # Only allow profile fields to be updated
        allowed_fields = {
            'first_name', 'last_name', 'phone', 'preferences', 
            'notification_settings', 'profile_picture_url'
        }
        
        profile_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        for field, value in profile_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_password(
        self,
        db: Session,
        *,
        user_id: UUID,
        hashed_password: str
    ) -> User:
        """
        Update user password with hashed password.
        """
        user = self.get(db, id=user_id)
        if user:
            user.hashed_password = hashed_password
            user.updated_at = datetime.utcnow()
            
            # Log password change activity
            self._log_activity(
                db,
                user_id=user_id,
                activity_type="password_changed",
                description="User password was changed"
            )
            
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
                return user
            except IntegrityError as e:
                db.rollback()
                raise e
        return None

    def update_role(self, db: Session, *, db_obj: User, new_role: str) -> User:
        """
        Update user role with activity logging.
        """
        old_role = db_obj.role
        db_obj.role = new_role
        db_obj.updated_at = datetime.utcnow()
        
        # Log role change activity
        self._log_activity(
            db,
            user_id=db_obj.id,
            activity_type="role_changed",
            description=f"Role changed from {old_role} to {new_role}"
        )
        
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_status(self, db: Session, *, db_obj: User, is_active: bool) -> User:
        """
        Update user active status with activity logging.
        """
        old_status = db_obj.is_active
        db_obj.is_active = is_active
        db_obj.updated_at = datetime.utcnow()
        
        # Log status change activity
        status_text = "activated" if is_active else "deactivated"
        self._log_activity(
            db,
            user_id=db_obj.id,
            activity_type="status_changed",
            description=f"User account {status_text}"
        )
        
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def update_current_unit(
        self,
        db: Session,
        *,
        user_id: UUID,
        unit_id: UUID
    ) -> Optional[User]:
        """
        Update user's current active unit preference.
        """
        user = self.get(db, id=user_id)
        if user:
            # Store current unit in user preferences
            if not user.preferences:
                user.preferences = {}
            
            user.preferences['current_unit_id'] = str(unit_id)
            user.updated_at = datetime.utcnow()
            
            db.add(user)
            
            try:
                db.commit()
                db.refresh(user)
                return user
            except IntegrityError as e:
                db.rollback()
                raise e
        
        return None

    def search_users(
        self,
        db: Session,
        *,
        search_query: str,
        unit_ids: Optional[List[UUID]] = None,
        role: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[List[User], int]:
        """
        Advanced user search with full-text capabilities.
        """
        search_term = f"%{search_query.lower()}%"
        
        query = db.query(User).options(
            joinedload(User.unit_assignments)
        )
        
        # Apply soft delete and active filters
        if hasattr(User, 'is_deleted'):
            query = query.filter(User.is_deleted == False)
        query = query.filter(User.is_active == True)
        
        # Filter by units if specified
        if unit_ids:
            query = query.join(UserUnitAssignment).filter(
                and_(
                    UserUnitAssignment.unit_id.in_(unit_ids),
                    UserUnitAssignment.is_active == True
                )
            )
        
        # Filter by role if specified
        if role:
            query = query.filter(User.role == role)
        
        # Search across multiple fields
        query = query.filter(
            or_(
                func.lower(User.first_name).like(search_term),
                func.lower(User.last_name).like(search_term),
                func.lower(User.email).like(search_term),
                func.concat(
                    func.lower(User.first_name), 
                    ' ', 
                    func.lower(User.last_name)
                ).like(search_term)
            )
        )
        
        query = query.distinct()
        total = query.count()
        
        # Order by relevance (name matches first, then email)
        users = query.order_by(
            func.lower(User.first_name).like(search_term).desc(),
            User.first_name.asc(),
            User.last_name.asc()
        ).limit(limit).all()
        
        return users, total

    def get_users_by_role(
        self,
        db: Session,
        *,
        role: str,
        unit_ids: Optional[List[UUID]] = None,
        is_active: bool = True
    ) -> List[User]:
        """Get all users with a specific role."""
        query = db.query(User).filter(User.role == role)
        
        if is_active:
            query = query.filter(User.is_active == True)
        
        if unit_ids:
            query = query.join(UserUnitAssignment).filter(
                and_(
                    UserUnitAssignment.unit_id.in_(unit_ids),
                    UserUnitAssignment.is_active == True
                )
            )
        
        if hasattr(User, 'is_deleted'):
            query = query.filter(User.is_deleted == False)
        
        return query.distinct().all()

    def get_user_statistics(
        self,
        db: Session,
        *,
        user_id: UUID,
        period: str = "month"
    ) -> UserStatsResponse:
        """
        Get user activity statistics for dashboard.
        """
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
            "user_id": user_id,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_orders": 0,
            "orders_approved": 0,
            "orders_rejected": 0,
            "total_spending": 0.0,
            "login_count": 0,
            "last_login": None,
            "active_sessions": 0,
            "productivity_score": 0.0
        }
        
        # Get user info
        user = self.get(db, id=user_id)
        if user:
            stats["last_login"] = user.last_login_at
        
        # Calculate activity-based statistics
        activity_count = db.query(UserActivity).filter(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.created_at >= start_date,
                UserActivity.created_at <= end_date
            )
        ).count()
        
        # Calculate login count from activities
        login_count = db.query(UserActivity).filter(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.activity_type == "login",
                UserActivity.created_at >= start_date,
                UserActivity.created_at <= end_date
            )
        ).count()
        
        stats["login_count"] = login_count
        stats["productivity_score"] = min(100.0, activity_count * 2.5)  # Simple productivity metric
        
        # Additional statistics would be calculated from order data
        # This is a placeholder for future implementation
        
        return UserStatsResponse(**stats)

    def get_user_activities(
        self,
        db: Session,
        *,
        user_id: UUID,
        limit: int = 50,
        activity_type: Optional[str] = None
    ) -> List[UserActivityResponse]:
        """
        Get user recent activity log.
        """
        query = db.query(UserActivity).filter(UserActivity.user_id == user_id)
        
        if activity_type:
            query = query.filter(UserActivity.activity_type == activity_type)
        
        activities = query.order_by(UserActivity.created_at.desc()).limit(limit).all()
        
        return [
            UserActivityResponse(
                id=activity.id,
                activity_type=activity.activity_type,
                description=activity.description,
                metadata=activity.metadata,
                created_at=activity.created_at,
                ip_address=activity.ip_address,
                user_agent=activity.user_agent
            )
            for activity in activities
        ]

    def log_user_activity(
        self,
        db: Session,
        *,
        user_id: UUID,
        activity_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserActivity:
        """
        Log user activity for audit trails.
        """
        return self._log_activity(
            db,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def update_last_login(self, db: Session, *, user_id: UUID, ip_address: Optional[str] = None) -> User:
        """
        Update user's last login timestamp and log activity.
        """
        user = self.get(db, id=user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            # Log login activity
            self._log_activity(
                db,
                user_id=user_id,
                activity_type="login",
                description="User logged in",
                ip_address=ip_address
            )
            
            db.add(user)
            
            try:
                db.commit()
                db.refresh(user)
                return user
            except IntegrityError as e:
                db.rollback()
                raise e
        
        return None

    def get_users_by_unit(
        self,
        db: Session,
        *,
        unit_id: UUID,
        role: Optional[str] = None,
        is_active: bool = True
    ) -> List[User]:
        """
        Get all users assigned to a specific unit.
        """
        query = db.query(User).join(UserUnitAssignment).filter(
            and_(
                UserUnitAssignment.unit_id == unit_id,
                UserUnitAssignment.is_active == True
            )
        )
        
        if role:
            query = query.filter(UserUnitAssignment.role == role)
        
        if is_active:
            query = query.filter(User.is_active == True)
        
        if hasattr(User, 'is_deleted'):
            query = query.filter(User.is_deleted == False)
        
        return query.distinct().all()

    def count_users_by_role(
        self,
        db: Session,
        *,
        role: str,
        unit_ids: Optional[List[UUID]] = None
    ) -> int:
        """
        Count users with a specific role.
        """
        query = db.query(User).filter(
            and_(
                User.role == role,
                User.is_active == True
            )
        )
        
        if unit_ids:
            query = query.join(UserUnitAssignment).filter(
                and_(
                    UserUnitAssignment.unit_id.in_(unit_ids),
                    UserUnitAssignment.is_active == True
                )
            )
        
        if hasattr(User, 'is_deleted'):
            query = query.filter(User.is_deleted == False)
        
        return query.distinct().count()

    def _log_activity(
        self,
        db: Session,
        *,
        user_id: UUID,
        activity_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        performed_by: Optional[UUID] = None
    ) -> UserActivity:
        """
        Internal method to log user activities.
        """
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            performed_by=performed_by or user_id,
            created_at=datetime.utcnow()
        )
        
        db.add(activity)
        
        try:
            # Don't commit here - let the calling method handle it
            db.flush()
            return activity
        except IntegrityError as e:
            db.rollback()
            raise e

    def bulk_update_role(
        self,
        db: Session,
        *,
        user_ids: List[UUID],
        new_role: str,
        updated_by: UUID
    ) -> int:
        """
        Update role for multiple users at once.
        """
        count = db.query(User).filter(User.id.in_(user_ids)).update(
            {
                'role': new_role,
                'updated_at': datetime.utcnow()
            },
            synchronize_session=False
        )
        
        # Log bulk role change activities
        for user_id in user_ids:
            self._log_activity(
                db,
                user_id=user_id,
                activity_type="role_changed",
                description=f"Role changed to {new_role} (bulk update)",
                performed_by=updated_by
            )
        
        try:
            db.commit()
            return count
        except IntegrityError as e:
            db.rollback()
            raise e

    def get_inactive_users(
        self,
        db: Session,
        *,
        days_inactive: int = 30,
        limit: int = 100
    ) -> List[User]:
        """
        Get users who haven't logged in for specified days.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        query = db.query(User).filter(
            or_(
                User.last_login_at < cutoff_date,
                User.last_login_at.is_(None)
            )
        ).filter(User.is_active == True)
        
        if hasattr(User, 'is_deleted'):
            query = query.filter(User.is_deleted == False)
        
        return query.order_by(User.last_login_at.asc().nullslast()).limit(limit).all()


# Create the CRUD instance
crud_user = CRUDUser(User)