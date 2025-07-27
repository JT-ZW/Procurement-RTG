from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import csv
import io
from datetime import datetime, timedelta

from app.api import deps
from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.supplier import Supplier
from app.schemas import supplier as supplier_schemas
from app.schemas.user import User as UserSchema
from app.crud.supplier import crud_supplier  
from app.utils.multi_tenant import get_user_units, check_unit_access
from app.api.deps import get_current_unit


router = APIRouter()


@router.get("/", response_model=supplier_schemas.SupplierList)
def get_suppliers(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    current_unit: Optional[UUID] = Depends(get_current_unit),
    skip: int = Query(0, ge=0, description="Number of suppliers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of suppliers to return"),
    search: Optional[str] = Query(None, description="Search term for supplier name or code"),
    status: Optional[str] = Query(None, regex="^(active|inactive|pending|suspended)$"),
    category: Optional[str] = Query(None, description="Filter by supplier category"),
    unit_id: Optional[UUID] = Query(None, description="Filter by specific unit"),
    sort_by: str = Query("company_name", regex="^(company_name|supplier_code|created_at|performance_score)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$")
) -> supplier_schemas.SupplierList:
    """
    Get suppliers with filtering, searching, and pagination.
    Access is filtered based on user's assigned units.
    """
    # Check user permissions
    accessible_units = get_user_units(db, current_user.id)
    
    # If unit_id is specified, ensure user has access
    if unit_id and unit_id not in accessible_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to specified unit"
        )
    
    # Filter by accessible units if not super admin
    unit_filter = None
    if current_user.role != "super_admin":
        if unit_id:
            unit_filter = [unit_id]
        else:
            unit_filter = accessible_units
    
    suppliers, total = crud_supplier.get_suppliers_with_filters(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        category=category,
        unit_ids=unit_filter,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return supplier_schemas.SupplierList(
        suppliers=suppliers,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        has_next=(skip + limit) < total,
        has_prev=skip > 0
    )


@router.post("/", response_model=supplier_schemas.Supplier, status_code=status.HTTP_201_CREATED)
def create_supplier(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_in: supplier_schemas.SupplierCreate,
    background_tasks: BackgroundTasks
) -> supplier_schemas.Supplier:
    """
    Create new supplier. Only procurement admins and super admins can create suppliers.
    """
    # Check permissions
    if current_user.role not in ["super_admin", "procurement_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create suppliers"
        )
    
    # Validate unit assignments
    if supplier_in.assigned_units:
        accessible_units = get_user_units(db, current_user.id)
        for unit_id in supplier_in.assigned_units:
            if unit_id not in accessible_units:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to unit {unit_id}"
                )
    
    # Check if supplier code already exists
    existing_supplier = crud_supplier.get_supplier_by_code(db, supplier_in.supplier_code)
    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier with this code already exists"
        )
    
    # Create supplier
    supplier = crud_supplier.create_supplier(db=db, obj_in=supplier_in, created_by=current_user.id)
    
    # Send welcome email if portal access is enabled (disabled for now)
    # if supplier_in.portal_access_enabled and supplier_in.contact_details.get("email"):
    #     background_tasks.add_task(
    #         email_helpers.send_supplier_welcome_email,
    #         supplier.contact_details["email"],
    #         supplier.company_name,
    #         supplier.supplier_code
    #     )
    
    return supplier


@router.get("/{supplier_id}", response_model=supplier_schemas.Supplier)
def get_supplier(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID
) -> supplier_schemas.Supplier:
    """
    Get supplier by ID with detailed information.
    """
    supplier = crud_supplier.get_supplier_with_details(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Check if user has access to any of supplier's units
    accessible_units = get_user_units(db, current_user.id)
    supplier_units = set(supplier.assigned_units)
    
    if (current_user.role not in ["super_admin", "procurement_admin"] and 
        not supplier_units.intersection(accessible_units)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this supplier"
        )
    
    return supplier


@router.put("/{supplier_id}", response_model=supplier_schemas.Supplier)
def update_supplier(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID,
    supplier_in: supplier_schemas.SupplierUpdate
) -> supplier_schemas.Supplier:
    """
    Update supplier information.
    """
    supplier = crud_supplier.get(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Check permissions
    if current_user.role not in ["super_admin", "procurement_admin"]:
        # Unit managers can only update suppliers assigned to their units
        accessible_units = get_user_units(db, current_user.id)
        supplier_units = set(supplier.assigned_units)
        
        if not supplier_units.intersection(accessible_units):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this supplier"
            )
    
    # Validate new unit assignments if provided
    if supplier_in.assigned_units is not None:
        accessible_units = get_user_units(db, current_user.id)
        for unit_id in supplier_in.assigned_units:
            if unit_id not in accessible_units:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to unit {unit_id}"
                )
    
    supplier = crud_supplier.update(db=db, db_obj=supplier, obj_in=supplier_in)
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID
):
    """
    Delete supplier. Only super admins can delete suppliers.
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete suppliers"
        )
    
    supplier = crud_supplier.get(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Check if supplier has active contracts or orders
    if crud_supplier.has_active_relationships(db, supplier_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete supplier with active contracts or orders"
        )
    
    crud_supplier.remove(db=db, id=supplier_id)


@router.get("/{supplier_id}/contracts", response_model=List[supplier_schemas.SupplierContract])
def get_supplier_contracts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID,
    status: Optional[str] = Query(None, regex="^(active|expired|pending|cancelled)$"),
    unit_id: Optional[UUID] = Query(None)
) -> List[supplier_schemas.SupplierContract]:
    """
    Get contracts for a specific supplier.
    """
    supplier = crud_supplier.get(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Check access permissions
    accessible_units = get_user_units(db, current_user.id)
    if unit_id and unit_id not in accessible_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to specified unit"
        )
    
    contracts = crud_supplier.get_supplier_contracts(
        db=db,
        supplier_id=supplier_id,
        status=status,
        unit_id=unit_id,
        accessible_units=accessible_units if current_user.role not in ["super_admin", "procurement_admin"] else None
    )
    
    return contracts


@router.post("/{supplier_id}/contracts", response_model=supplier_schemas.SupplierContract, status_code=status.HTTP_201_CREATED)
def create_supplier_contract(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID,
    contract_in: supplier_schemas.SupplierContractCreate
) -> supplier_schemas.SupplierContract:
    """
    Create new contract for supplier.
    """
    if current_user.role not in ["super_admin", "procurement_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create contracts"
        )
    
    supplier = crud_supplier.get(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Validate unit assignments
    accessible_units = get_user_units(db, current_user.id)
    for unit_id in contract_in.unit_assignments:
        if unit_id not in accessible_units:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to unit {unit_id}"
            )
    
    contract = crud_supplier.create_contract(
        db=db,
        supplier_id=supplier_id,
        contract_in=contract_in,
        created_by=current_user.id
    )
    
    return contract


@router.get("/{supplier_id}/performance", response_model=supplier_schemas.SupplierPerformance)
def get_supplier_performance(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    unit_id: Optional[UUID] = Query(None)
) -> supplier_schemas.SupplierPerformance:
    """
    Get supplier performance metrics.
    """
    supplier = crud_supplier.get(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=90)  # Default to last 90 days
    
    # Check access permissions
    accessible_units = get_user_units(db, current_user.id)
    if unit_id and unit_id not in accessible_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to specified unit"
        )
    
    performance = crud_supplier.get_performance_metrics(
        db=db,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date,
        unit_id=unit_id,
        accessible_units=accessible_units if current_user.role not in ["super_admin", "procurement_admin"] else None
    )
    
    return performance


@router.post("/{supplier_id}/assign-units", response_model=supplier_schemas.Supplier)
def assign_supplier_to_units(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: UUID,
    unit_assignment: supplier_schemas.SupplierUnitAssignment
) -> supplier_schemas.Supplier:
    """
    Assign supplier to specific units.
    """
    if current_user.role not in ["super_admin", "procurement_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign suppliers to units"
        )
    
    supplier = crud_supplier.get(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Validate unit access
    accessible_units = get_user_units(db, current_user.id)
    for unit_id in unit_assignment.unit_ids:
        if unit_id not in accessible_units:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to unit {unit_id}"
            )
    
    supplier = crud_supplier.assign_to_units(
        db=db,
        supplier_id=supplier_id,
        unit_ids=unit_assignment.unit_ids,
        assigned_by=current_user.id
    )
    
    return supplier


@router.post("/import", response_model=supplier_schemas.SupplierImportResult)
def import_suppliers_csv(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    unit_id: Optional[UUID] = Query(None, description="Default unit assignment for imported suppliers"),
    validate_only: bool = Query(False, description="Only validate data without importing")
) -> supplier_schemas.SupplierImportResult:
    """
    Import suppliers from CSV file.
    """
    if current_user.role not in ["super_admin", "procurement_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to import suppliers"
        )
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    # Validate unit access if specified
    if unit_id:
        accessible_units = get_user_units(db, current_user.id)
        if unit_id not in accessible_units:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to specified unit"
            )
    
    # CSV import functionality temporarily disabled
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="CSV import functionality is not yet implemented"
    )


@router.get("/export/csv")
def export_suppliers_csv(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    unit_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    format: str = Query("csv", regex="^(csv|xlsx)$")
):
    """
    Export suppliers to CSV or Excel format.
    """
    # Check permissions and get accessible units
    accessible_units = get_user_units(db, current_user.id)
    
    if unit_id and unit_id not in accessible_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to specified unit"
        )
    
    # Get suppliers data
    suppliers = crud_supplier.get_suppliers_for_export(
        db=db,
        unit_id=unit_id,
        status=status,
        accessible_units=accessible_units if current_user.role not in ["super_admin", "procurement_admin"] else None
    )
    
    # CSV/Excel export functionality temporarily disabled
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Export functionality is not yet implemented"
    )


@router.post("/bulk-operations", response_model=supplier_schemas.BulkOperationResult)
def bulk_supplier_operations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    operation: supplier_schemas.SupplierBulkOperation
) -> supplier_schemas.BulkOperationResult:
    """
    Perform bulk operations on multiple suppliers.
    """
    if current_user.role not in ["super_admin", "procurement_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for bulk operations"
        )
    
    # Validate access to all suppliers
    accessible_units = get_user_units(db, current_user.id)
    for supplier_id in operation.supplier_ids:
        supplier = crud_supplier.get(db, supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier {supplier_id} not found"
            )
        
        # Check if user has access to any of supplier's units
        if (current_user.role not in ["super_admin", "procurement_admin"] and 
            not set(supplier.assigned_units).intersection(accessible_units)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to supplier {supplier_id}"
            )
    
    # Perform bulk operation
    result = crud_supplier.bulk_operation(
        db=db,
        supplier_ids=operation.supplier_ids,
        operation=operation.operation,
        data=operation.data,
        performed_by=current_user.id
    )
    
    return result


@router.get("/summary/stats", response_model=supplier_schemas.SupplierStats)
def get_supplier_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_active_user),
    unit_id: Optional[UUID] = Query(None)
) -> supplier_schemas.SupplierStats:
    """
    Get supplier statistics and metrics.
    """
    # Check unit access
    accessible_units = get_user_units(db, current_user.id)
    if unit_id and unit_id not in accessible_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to specified unit"
        )
    
    stats = crud_supplier.get_supplier_statistics(
        db=db,
        unit_id=unit_id,
        accessible_units=accessible_units if current_user.role not in ["super_admin", "procurement_admin"] else None
    )
    
    return stats
