from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base


class ProductCategory(Base):
    """
    Product categories for organizational hierarchy.
    """
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    
    # Hierarchy and display
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship("ProductCategory", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")

    # Indexes
    __table_args__ = (
        Index('idx_product_category_name', 'name'),
        Index('idx_product_category_active', 'is_active'),
        Index('idx_product_category_parent', 'parent_id'),
    )

    def __repr__(self):
        return f"<ProductCategory(id='{self.id}', name='{self.name}')>"


class Product(Base):
    """
    Main product model representing items that can be procured.
    Products are allocated to specific hotel units with different stock levels and suppliers.
    """
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic product information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    sku = Column(String(100), nullable=False, unique=True, index=True)
    brand = Column(String(100))
    model_number = Column(String(100))
    
    # Category relationship
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    
    # Product specifications
    unit_of_measure = Column(String(50), nullable=False, default="each")  # each, kg, liter, box, etc.
    pack_size = Column(Integer, default=1)  # Number of units per pack
    dimensions = Column(JSONB)  # {"length": 10, "width": 5, "height": 3, "unit": "cm"}
    weight = Column(Numeric(10, 3))  # Weight in kg
    
    # Product classification
    is_perishable = Column(Boolean, default=False)
    is_hazardous = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)  # High-value items requiring approval
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_discontinued = Column(Boolean, default=False)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    tags = Column(JSONB)  # ["organic", "local", "premium"]
    custom_attributes = Column(JSONB)  # Flexible attributes for specific product types
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    unit_allocations = relationship("ProductUnitAllocation", back_populates="product", cascade="all, delete-orphan")
    supplier_relationships = relationship("ProductSupplier", back_populates="product", cascade="all, delete-orphan")
    
    # User relationships for audit
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Constraints
    __table_args__ = (
        CheckConstraint('pack_size > 0', name='chk_product_pack_size_positive'),
        CheckConstraint('weight IS NULL OR weight >= 0', name='chk_product_weight_non_negative'),
        Index('idx_product_name', 'name'),
        Index('idx_product_sku', 'sku'),
        Index('idx_product_brand', 'brand'),
        Index('idx_product_category', 'category_id'),
        Index('idx_product_active', 'is_active'),
        Index('idx_product_deleted', 'is_deleted'),
        Index('idx_product_created_at', 'created_at'),
        Index('idx_product_search', 'name', 'description', 'sku', 'brand'),  # Composite index for search
    )

    def __repr__(self):
        return f"<Product(id='{self.id}', name='{self.name}', sku='{self.sku}')>"


class ProductUnitAllocation(Base):
    """
    Multi-tenant allocation of products to hotel units with unit-specific stock management.
    This enables the same product to have different stock levels and settings per unit.
    """
    __tablename__ = "product_unit_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Stock management
    current_stock = Column(Integer, default=0, nullable=False)
    min_stock_level = Column(Integer, default=0, nullable=False)
    max_stock_level = Column(Integer, default=100, nullable=False)
    reorder_point = Column(Integer, default=10, nullable=False)
    reorder_quantity = Column(Integer, default=50, nullable=False)
    
    # Location within unit
    storage_location = Column(String(100))  # "Kitchen Store Room", "Bar Storage", etc.
    bin_location = Column(String(50))  # Specific bin or shelf location
    
    # Unit-specific settings
    is_authorized = Column(Boolean, default=True)  # Whether unit is authorized to order this product
    requires_unit_approval = Column(Boolean, default=False)  # Unit-specific approval requirement
    
    # Cost and budgeting (unit-specific)
    last_cost = Column(Numeric(10, 2))  # Last purchase cost for this unit
    average_cost = Column(Numeric(10, 2))  # Rolling average cost
    budget_category = Column(String(50))  # "F&B", "Housekeeping", "Maintenance", etc.
    
    # Stock tracking
    last_counted_at = Column(DateTime(timezone=True))
    last_counted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    variance_threshold = Column(Integer, default=5)  # Alert if variance > threshold
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())  # For stock updates
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    product = relationship("Product", back_populates="unit_allocations")
    unit = relationship("Unit")
    counter = relationship("User", foreign_keys=[last_counted_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one allocation per product per unit
        Index('idx_product_unit_unique', 'product_id', 'unit_id', unique=True),
        CheckConstraint('current_stock >= 0', name='chk_current_stock_non_negative'),
        CheckConstraint('min_stock_level >= 0', name='chk_min_stock_non_negative'),
        CheckConstraint('max_stock_level >= min_stock_level', name='chk_max_stock_gte_min'),
        CheckConstraint('reorder_point >= 0', name='chk_reorder_point_non_negative'),
        CheckConstraint('reorder_quantity > 0', name='chk_reorder_quantity_positive'),
        CheckConstraint('variance_threshold >= 0', name='chk_variance_threshold_non_negative'),
        Index('idx_product_allocation_product', 'product_id'),
        Index('idx_product_allocation_unit', 'unit_id'),
        Index('idx_product_allocation_stock_level', 'current_stock'),
        Index('idx_product_allocation_reorder', 'current_stock', 'reorder_point'),  # For low stock queries
        Index('idx_product_allocation_budget', 'budget_category'),
    )

    @property
    def needs_reorder(self) -> bool:
        """Check if product needs reordering based on current stock and reorder point."""
        return self.current_stock <= self.reorder_point

    @property
    def stock_status(self) -> str:
        """Get stock status as string."""
        if self.current_stock <= 0:
            return "out_of_stock"
        elif self.current_stock <= self.reorder_point:
            return "low_stock"
        elif self.current_stock >= self.max_stock_level:
            return "overstock"
        else:
            return "normal"

    def __repr__(self):
        return f"<ProductUnitAllocation(product_id='{self.product_id}', unit_id='{self.unit_id}', stock={self.current_stock})>"


class ProductSupplier(Base):
    """
    Many-to-many relationship between products, suppliers, and units.
    Enables different suppliers per unit for the same product with unit-specific pricing.
    """
    __tablename__ = "product_suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Supplier designation
    is_primary_supplier = Column(Boolean, default=False)  # Primary supplier for this unit
    priority_order = Column(Integer, default=1)  # 1 = first choice, 2 = second choice, etc.
    
    # Pricing information
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    price_per_unit = Column(String(50))  # "per piece", "per kg", "per case"
    
    # Contract and terms
    contract_reference = Column(String(100))
    effective_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    
    # Order terms
    minimum_order_quantity = Column(Integer, default=1)
    maximum_order_quantity = Column(Integer)
    order_multiple = Column(Integer, default=1)  # Must order in multiples of this number
    
    # Delivery and logistics
    lead_time_days = Column(Integer, default=7)
    delivery_schedule = Column(JSONB)  # {"monday": true, "tuesday": false, ...}
    shipping_cost = Column(Numeric(10, 2))
    free_shipping_threshold = Column(Numeric(10, 2))
    
    # Performance tracking
    quality_rating = Column(Numeric(3, 2))  # 1.00 to 5.00
    delivery_rating = Column(Numeric(3, 2))  # 1.00 to 5.00
    service_rating = Column(Numeric(3, 2))  # 1.00 to 5.00
    last_order_date = Column(DateTime(timezone=True))
    total_orders = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_preferred = Column(Boolean, default=False)  # Preferred supplier flag
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional terms and notes
    payment_terms = Column(String(100))  # "Net 30", "Cash on Delivery", etc.
    special_terms = Column(Text)
    notes = Column(Text)
    
    # Relationships
    product = relationship("Product", back_populates="supplier_relationships")
    supplier = relationship("Supplier")
    unit = relationship("Unit")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one relationship per product-supplier-unit combination
        Index('idx_product_supplier_unit_unique', 'product_id', 'supplier_id', 'unit_id', unique=True),
        CheckConstraint('price >= 0', name='chk_price_non_negative'),
        CheckConstraint('minimum_order_quantity > 0', name='chk_min_order_qty_positive'),
        CheckConstraint('maximum_order_quantity IS NULL OR maximum_order_quantity >= minimum_order_quantity', 
                       name='chk_max_order_qty_gte_min'),
        CheckConstraint('order_multiple > 0', name='chk_order_multiple_positive'),
        CheckConstraint('lead_time_days >= 0', name='chk_lead_time_non_negative'),
        CheckConstraint('quality_rating IS NULL OR (quality_rating >= 1.0 AND quality_rating <= 5.0)', 
                       name='chk_quality_rating_range'),
        CheckConstraint('delivery_rating IS NULL OR (delivery_rating >= 1.0 AND delivery_rating <= 5.0)', 
                       name='chk_delivery_rating_range'),
        CheckConstraint('service_rating IS NULL OR (service_rating >= 1.0 AND service_rating <= 5.0)', 
                       name='chk_service_rating_range'),
        CheckConstraint('priority_order > 0', name='chk_priority_order_positive'),
        Index('idx_product_supplier_product', 'product_id'),
        Index('idx_product_supplier_supplier', 'supplier_id'),
        Index('idx_product_supplier_unit', 'unit_id'),
        Index('idx_product_supplier_primary', 'is_primary_supplier'),
        Index('idx_product_supplier_active', 'is_active'),
        Index('idx_product_supplier_price', 'price'),
        Index('idx_product_supplier_priority', 'priority_order'),
        Index('idx_product_supplier_contract', 'contract_reference'),
        Index('idx_product_supplier_expiry', 'expiry_date'),
    )

    @property
    def is_contract_active(self) -> bool:
        """Check if contract is currently active based on effective and expiry dates."""
        now = datetime.utcnow()
        if self.effective_date and now < self.effective_date:
            return False
        if self.expiry_date and now > self.expiry_date:
            return False
        return True

    @property
    def overall_rating(self) -> float:
        """Calculate overall supplier rating as average of quality, delivery, and service ratings."""
        ratings = [r for r in [self.quality_rating, self.delivery_rating, self.service_rating] if r is not None]
        if not ratings:
            return 0.0
        return sum(ratings) / len(ratings)

    def __repr__(self):
        return f"<ProductSupplier(product_id='{self.product_id}', supplier_id='{self.supplier_id}', unit_id='{self.unit_id}', price={self.price})>"


class ProductMovement(Base):
    """
    Track product stock movements for audit and inventory management.
    Records all stock changes (receipts, issues, adjustments, transfers).
    """
    __tablename__ = "product_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    # Movement details
    movement_type = Column(String(50), nullable=False)  # "receipt", "issue", "adjustment", "transfer_in", "transfer_out"
    quantity = Column(Integer, nullable=False)  # Positive for increases, negative for decreases
    unit_cost = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))
    
    # Stock levels
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    
    # Reference information
    reference_type = Column(String(50))  # "purchase_order", "requisition", "adjustment", "transfer"
    reference_id = Column(UUID(as_uuid=True))  # ID of the source document
    reference_number = Column(String(100))  # Human-readable reference number
    
    # Additional details
    reason = Column(String(200))  # Reason for movement
    batch_number = Column(String(100))
    expiry_date = Column(DateTime(timezone=True))
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    
    # Location information
    from_location = Column(String(100))
    to_location = Column(String(100))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    product = relationship("Product")
    unit = relationship("Unit")
    supplier = relationship("Supplier")
    creator = relationship("User")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('quantity != 0', name='chk_movement_quantity_not_zero'),
        CheckConstraint('previous_stock >= 0', name='chk_previous_stock_non_negative'),
        CheckConstraint('new_stock >= 0', name='chk_new_stock_non_negative'),
        CheckConstraint('previous_stock + quantity = new_stock', name='chk_stock_calculation'),
        Index('idx_product_movement_product', 'product_id'),
        Index('idx_product_movement_unit', 'unit_id'),
        Index('idx_product_movement_type', 'movement_type'),
        Index('idx_product_movement_created', 'created_at'),
        Index('idx_product_movement_reference', 'reference_type', 'reference_id'),
        Index('idx_product_movement_batch', 'batch_number'),
        Index('idx_product_movement_supplier', 'supplier_id'),
    )

    def __repr__(self):
        return f"<ProductMovement(product_id='{self.product_id}', type='{self.movement_type}', quantity={self.quantity})>"