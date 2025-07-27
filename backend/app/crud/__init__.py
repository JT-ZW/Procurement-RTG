"""
CRUD operations module
Exports all CRUD instances for the application.
"""

from app.crud.base import CRUDBase

# Import individual CRUD classes and instances
try:
    from app.crud.user import crud_user
except ImportError:
    crud_user = None

try:
    from app.crud.unit import crud_unit
except ImportError:
    crud_unit = None

try:
    from app.crud.product import crud_product
except ImportError:
    crud_product = None

try:
    from app.crud.supplier import crud_supplier
except ImportError:
    crud_supplier = None

try:
    from app.crud.requisition import (
        requisition_crud,
        requisition_item_crud,
        requisition_approval_crud, 
        requisition_comment_crud
    )
except ImportError:
    requisition_crud = None
    requisition_item_crud = None
    requisition_approval_crud = None
    requisition_comment_crud = None

# Export all CRUD instances
__all__ = [
    "CRUDBase",
    "crud_user",
    "crud_unit", 
    "crud_product",
    "crud_supplier",
    "requisition_crud",
    "requisition_item_crud",
    "requisition_approval_crud",
    "requisition_comment_crud"
]
