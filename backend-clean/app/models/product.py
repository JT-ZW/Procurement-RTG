"""
Product Model - Enhanced E-catalogue product management
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Product(Base):
    """Enhanced Product model for E-catalogue inventory management."""
    __tablename__ = "products"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Category relationship
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    
    # Unit and Supplier relationships
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    
    # Product specifications
    unit_of_measure = Column(String(50), nullable=False, default="pieces")
    specifications = Column(JSONB)
    
    # Pricing - E-catalogue requirements
    standard_cost = Column(Numeric(10, 2))  # Standard unit price
    contract_price = Column(Numeric(10, 2))  # Contract-specific price
    currency = Column(String(3), default="USD")
    
    # Stock management - E-catalogue requirements
    current_stock_quantity = Column(Numeric(10, 3), default=0)
    minimum_stock_level = Column(Integer, default=0, nullable=False)
    maximum_stock_level = Column(Integer, default=1000, nullable=False)
    reorder_point = Column(Integer, default=10, nullable=False)
    
    # Consumption tracking - E-catalogue requirements
    estimated_consumption_rate_per_day = Column(Numeric(10, 3), default=0)
    last_restocked_date = Column(DateTime(timezone=True))
    last_consumption_update = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    unit = relationship("Unit", backref="products")
    category = relationship("ProductCategory", backref="products")
    supplier = relationship("Supplier", backref="products")
    
    @property
    def effective_unit_price(self):
        """Return contract price if available, otherwise standard cost"""
        return self.contract_price if self.contract_price else self.standard_cost
    
    @property
    def estimated_days_stock_will_last(self):
        """Calculate estimated days the current stock will last"""
        if self.estimated_consumption_rate_per_day and self.estimated_consumption_rate_per_day > 0:
            return round(float(self.current_stock_quantity) / float(self.estimated_consumption_rate_per_day), 2)
        return None
    
    @property 
    def stock_status(self):
        """Determine current stock status"""
        if self.current_stock_quantity <= self.minimum_stock_level:
            return "LOW_STOCK"
        elif self.current_stock_quantity <= self.reorder_point:
            return "REORDER_NEEDED"
        elif self.current_stock_quantity >= self.maximum_stock_level:
            return "OVERSTOCK"
        else:
            return "NORMAL"
    
    def __repr__(self):
        return f"<Product {self.code}: {self.name}>"


class ProductCategory(Base):
    """Product Category model for organizing products"""
    __tablename__ = "product_categories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Hierarchical structure
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Self-referential relationship
    subcategories = relationship("ProductCategory", backref="parent_category", remote_side=[id])
    
    def __repr__(self):
        return f"<ProductCategory {self.code}: {self.name}>"
