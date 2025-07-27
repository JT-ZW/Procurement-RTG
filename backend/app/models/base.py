"""
Base models and shared functionality for all models.
This file imports all model classes so they can be discovered by Alembic.
"""

from app.core.database import Base

# Import all models here so they are discovered by Alembic
from app.models.user import User, UserUnitAssignment
from app.models.unit import Unit
from app.models.product import Product
from app.models.supplier import Supplier

# Export Base and all models
__all__ = [
    "Base",
    "User", 
    "UserUnitAssignment",
    "Unit",
    "Product",
    "Supplier"
]
