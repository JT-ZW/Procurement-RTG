"""
Database models module
"""

# Import base class first
from app.models.base import Base

# Import all models
from app.models.user import User, UserUnitAssignment
from app.models.unit import Unit, UnitConfig
from app.models.product import Product, ProductCategory, ProductMovement
from app.models.supplier import Supplier, SupplierContact, SupplierContract, SupplierUnitRelationship, SupplierPerformance

# Import new procurement workflow models
from app.models.purchase_requisition import (
    PurchaseRequisition, 
    RequisitionItem, 
    RequisitionApproval, 
    RequisitionComment
)
from app.models.purchase_order import (
    PurchaseOrder, 
    PurchaseOrderItem, 
    PurchaseOrderStatusHistory
)
from app.models.quotation import (
    RequestForQuotation, 
    RFQItem, 
    SupplierQuote, 
    QuoteItem, 
    QuoteEvaluation
)
from app.models.budget_approval import (
    Budget, 
    BudgetAllocation, 
    BudgetTransaction, 
    ApprovalWorkflow, 
    ApprovalLevel, 
    ApprovalRequest
)
from app.models.invoice_payment import (
    Invoice, 
    InvoiceLineItem, 
    Payment, 
    InvoiceStatusHistory
)
from app.models.notification import (
    Notification, 
    NotificationTemplate, 
    NotificationDeliveryLog, 
    NotificationPreference, 
    NotificationRule
)

# Export all models for Alembic autogenerate
__all__ = [
    "Base",
    # Core models
    "User",
    "UserUnitAssignment", 
    "Unit",
    "UnitConfig",
    "Product",
    "ProductCategory",
    "ProductMovement",
    "Supplier",
    "SupplierContact",
    "SupplierContract",
    "SupplierUnitRelationship",
    "SupplierPerformance",
    # Procurement workflow models
    "PurchaseRequisition",
    "RequisitionItem",
    "RequisitionApproval",
    "RequisitionComment",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "PurchaseOrderStatusHistory",
    "RequestForQuotation",
    "RFQItem",
    "SupplierQuote",
    "QuoteItem",
    "QuoteEvaluation",
    "Budget",
    "BudgetAllocation",
    "BudgetTransaction",
    "ApprovalWorkflow",
    "ApprovalLevel",
    "ApprovalRequest",
    "Invoice",
    "InvoiceLineItem",
    "Payment",
    "InvoiceStatusHistory",
    "Notification",
    "NotificationTemplate",
    "NotificationDeliveryLog",
    "NotificationPreference",
    "NotificationRule"
]
