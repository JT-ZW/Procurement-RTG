from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        """
        query = db.query(self.model).filter(self.model.id == id)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        return query.first()

    def get_by_ids(self, db: Session, ids: List[Any]) -> List[ModelType]:
        """
        Get multiple records by IDs.
        """
        query = db.query(self.model).filter(self.model.id.in_(ids))
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        return query.all()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        """
        query = db.query(self.model)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                order_column = order_column.desc()
            query = query.order_by(order_column)
        elif hasattr(self.model, 'created_at'):
            # Default ordering by creation date (newest first)
            query = query.order_by(self.model.created_at.desc())
        
        return query.offset(skip).limit(limit).all()

    def get_multi_with_total(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> tuple[List[ModelType], int]:
        """
        Get multiple records with pagination and total count.
        """
        query = db.query(self.model)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    column = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                order_column = order_column.desc()
            query = query.order_by(order_column)
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        return items, total

    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Create a new record.
        """
        obj_in_data = jsonable_encoder(obj_in)
        
        # Add any additional kwargs (like created_by, etc.)
        obj_in_data.update(kwargs)
        
        # Set timestamps if model supports them
        if hasattr(self.model, 'created_at'):
            obj_in_data['created_at'] = datetime.utcnow()
        if hasattr(self.model, 'updated_at'):
            obj_in_data['updated_at'] = datetime.utcnow()
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def create_multi(
        self, 
        db: Session, 
        *, 
        objs_in: List[CreateSchemaType], 
        **kwargs
    ) -> List[ModelType]:
        """
        Create multiple records in bulk.
        """
        db_objs = []
        current_time = datetime.utcnow()
        
        for obj_in in objs_in:
            obj_in_data = jsonable_encoder(obj_in)
            obj_in_data.update(kwargs)
            
            # Set timestamps if model supports them
            if hasattr(self.model, 'created_at'):
                obj_in_data['created_at'] = current_time
            if hasattr(self.model, 'updated_at'):
                obj_in_data['updated_at'] = current_time
            
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        
        try:
            db.commit()
            for db_obj in db_objs:
                db.refresh(db_obj)
            return db_objs
        except IntegrityError as e:
            db.rollback()
            raise e

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record.
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        # Set updated timestamp if model supports it
        if hasattr(self.model, 'updated_at'):
            update_data['updated_at'] = datetime.utcnow()
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        Delete a record (soft delete if supported, otherwise hard delete).
        """
        obj = db.query(self.model).get(id)
        if not obj:
            return None
        
        # Soft delete if model supports it
        if hasattr(self.model, 'is_deleted'):
            obj.is_deleted = True
            if hasattr(self.model, 'deleted_at'):
                obj.deleted_at = datetime.utcnow()
            if hasattr(self.model, 'updated_at'):
                obj.updated_at = datetime.utcnow()
            db.add(obj)
        elif hasattr(self.model, 'deleted_at'):
            obj.deleted_at = datetime.utcnow()
            if hasattr(self.model, 'updated_at'):
                obj.updated_at = datetime.utcnow()
            db.add(obj)
        else:
            # Hard delete
            db.delete(obj)
        
        try:
            db.commit()
            return obj
        except IntegrityError as e:
            db.rollback()
            raise e

    def remove_multi(self, db: Session, *, ids: List[Any]) -> int:
        """
        Delete multiple records by IDs.
        """
        query = db.query(self.model).filter(self.model.id.in_(ids))
        
        # Soft delete if model supports it
        if hasattr(self.model, 'is_deleted'):
            update_data = {'is_deleted': True}
            if hasattr(self.model, 'deleted_at'):
                update_data['deleted_at'] = datetime.utcnow()
            if hasattr(self.model, 'updated_at'):
                update_data['updated_at'] = datetime.utcnow()
            
            count = query.update(update_data, synchronize_session=False)
        elif hasattr(self.model, 'deleted_at'):
            update_data = {'deleted_at': datetime.utcnow()}
            if hasattr(self.model, 'updated_at'):
                update_data['updated_at'] = datetime.utcnow()
            
            count = query.update(update_data, synchronize_session=False)
        else:
            # Hard delete
            count = query.delete(synchronize_session=False)
        
        try:
            db.commit()
            return count
        except IntegrityError as e:
            db.rollback()
            raise e

    def restore(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        """
        if not (hasattr(self.model, 'is_deleted') or hasattr(self.model, 'deleted_at')):
            raise ValueError("Model does not support soft delete")
        
        query = db.query(self.model).filter(self.model.id == id)
        
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == True)
            obj = query.first()
            if obj:
                obj.is_deleted = False
                if hasattr(self.model, 'deleted_at'):
                    obj.deleted_at = None
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.isnot(None))
            obj = query.first()
            if obj:
                obj.deleted_at = None
        
        if obj:
            if hasattr(self.model, 'updated_at'):
                obj.updated_at = datetime.utcnow()
            db.add(obj)
            
            try:
                db.commit()
                db.refresh(obj)
                return obj
            except IntegrityError as e:
                db.rollback()
                raise e
        
        return None

    def exists(self, db: Session, *, id: Any) -> bool:
        """
        Check if a record exists by ID.
        """
        query = db.query(self.model.id).filter(self.model.id == id)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        return query.first() is not None

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters.
        """
        query = db.query(self.model)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    column = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        
        return query.count()

    def search(
        self,
        db: Session,
        *,
        search_query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[ModelType], int]:
        """
        Search records across multiple fields.
        """
        query = db.query(self.model)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply search filters
        if search_query and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    # Case-insensitive search
                    search_conditions.append(
                        func.lower(column).contains(search_query.lower())
                    )
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    column = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        if hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        
        items = query.offset(skip).limit(limit).all()
        
        return items, total

    def get_or_create(
        self,
        db: Session,
        *,
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> tuple[ModelType, bool]:
        """
        Get an existing record or create a new one.
        Returns (instance, created) where created is a boolean.
        """
        query = db.query(self.model)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply lookup filters
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        instance = query.first()
        
        if instance:
            return instance, False
        
        # Create new instance
        create_data = kwargs.copy()
        if defaults:
            create_data.update(defaults)
        
        # Set timestamps if model supports them
        if hasattr(self.model, 'created_at'):
            create_data['created_at'] = datetime.utcnow()
        if hasattr(self.model, 'updated_at'):
            create_data['updated_at'] = datetime.utcnow()
        
        instance = self.model(**create_data)
        db.add(instance)
        
        try:
            db.commit()
            db.refresh(instance)
            return instance, True
        except IntegrityError as e:
            db.rollback()
            raise e

    def bulk_update(
        self,
        db: Session,
        *,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """
        Update multiple records matching filters.
        """
        query = db.query(self.model)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                if isinstance(value, list):
                    query = query.filter(column.in_(value))
                else:
                    query = query.filter(column == value)
        
        # Add updated timestamp
        if hasattr(self.model, 'updated_at'):
            update_data['updated_at'] = datetime.utcnow()
        
        count = query.update(update_data, synchronize_session=False)
        
        try:
            db.commit()
            return count
        except IntegrityError as e:
            db.rollback()
            raise e

    def get_by_field(
        self, 
        db: Session, 
        *, 
        field: str, 
        value: Any, 
        first_only: bool = True
    ) -> Union[ModelType, List[ModelType], None]:
        """
        Get record(s) by a specific field value.
        """
        if not hasattr(self.model, field):
            raise ValueError(f"Model {self.model.__name__} does not have field '{field}'")
        
        query = db.query(self.model).filter(getattr(self.model, field) == value)
        
        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        elif hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        
        if first_only:
            return query.first()
        else:
            return query.all()