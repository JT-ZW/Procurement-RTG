"""
Unit Model - Hotel/Property units for multi-tenant architecture
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Unit(Base):
    """Hotel unit/property model for multi-tenant support."""
    __tablename__ = "units"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "HOTEL001"
    description = Column(Text)
    
    # Location
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Unit {self.code}: {self.name}>"
