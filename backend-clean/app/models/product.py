"""
Product Model - Basic product catalog
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Product(Base):
    """Product model for inventory management."""
    __tablename__ = "products"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Unit assignment
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Pricing
    price = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    unit = relationship("Unit", backref="products")
    
    def __repr__(self):
        return f"<Product {self.code}: {self.name}>"
