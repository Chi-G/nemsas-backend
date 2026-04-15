from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.ambulance import (
    Ambulance, AmbulanceCreate, AmbulanceUpdate, GPSHistoryCreate,
    FleetFilter, BulkUploadReport, AmbulanceAllocation
)
from src.services.ambulance import ambulance_service
from src.db.models.user import User
from src.db.models.ambulance import AmbulanceStatus
from src.core.rbac import Permission as PermissionEnum

router = APIRouter()

@router.get("/", response_model=List[Ambulance])
async def search_ambulances(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    accreditation_type: Optional[str] = Query(None),
    status: Optional[AmbulanceStatus] = Query(None),
    state_id: Optional[int] = Query(None),
    lga_id: Optional[int] = Query(None),
    partner_id: Optional[int] = Query(None),
    facility_id: Optional[int] = Query(None),
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_READ])),
    state_scope: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Search and list ambulances with filters. (Admins, Dispatchers, Partners)
    """
    filters = FleetFilter(
        accreditation_type=accreditation_type,
        status=status,
        state_id=state_id,
        lga_id=lga_id,
        partner_id=partner_id,
        facility_id=facility_id
    )
    return await ambulance_service.list_ambulances(
        db, filters=filters, skip=skip, limit=limit, state_id=state_scope
    )

@router.post("/", response_model=Ambulance)
async def create_ambulance(
    *,
    db: AsyncSession = Depends(get_db),
    ambulance_in: AmbulanceCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Register a new ambulance. (Admins, ETPs)
    """
    if state_id and ambulance_in.state_id != state_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SEMSAS Admins can only register ambulances in their assigned state"
        )
    try:
        return await ambulance_service.create(db, obj_in=ambulance_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/template")
async def get_ambulance_template(
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_MANAGE])),
) -> Any:
    """
    Download CSV template for bulk ambulance upload.
    """
    csv_content = ambulance_service.generate_csv_template()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ambulance_template.csv"}
    )

@router.post("/bulk-upload/validate", response_model=BulkUploadReport)
async def validate_bulk_upload(
    *,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_MANAGE])),
) -> Any:
    """
    Validate a CSV file for bulk ambulance registration.
    """
    content = await file.read()
    return await ambulance_service.bulk_validate_csv(db, csv_content=content.decode())

@router.post("/bulk-upload/confirm", response_model=List[Ambulance])
async def confirm_bulk_upload(
    *,
    db: AsyncSession = Depends(get_db),
    data: List[dict],
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_MANAGE])),
) -> Any:
    """
    Finalize registration of ambulances from validated list.
    """
    # If the user is a partner, we force their partner_id
    # This logic depends on how partners are identified (user_id/partner_id mapping)
    # For now we assume the data contains IDs or the service handles it.
    return await ambulance_service.bulk_commit(db, data_list=data)

@router.get("/{id}", response_model=Ambulance)
async def read_ambulance(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get ambulance by ID.
    """
    ambulance = await ambulance_service.get_by_id(db, ambulance_id=id, state_id=state_id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found or access denied")
    return ambulance

@router.patch("/{id}/status", response_model=Ambulance)
async def update_ambulance_status(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    status_in: AmbulanceStatus = Body(...),
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Update ambulance status. (Admins, Dispatchers)
    """
    ambulance = await ambulance_service.get_by_id(db, ambulance_id=id, state_id=state_id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found or access denied")
    return await ambulance_service.update_status(db, db_obj=ambulance, new_status=status_in)

@router.post("/{id}/allocate", response_model=Ambulance)
async def allocate_ambulance(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    allocation: AmbulanceAllocation,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Allocate an ambulance to a health facility.
    """
    # Check if ambulance exists and in scope
    ambulance = await ambulance_service.get_by_id(db, ambulance_id=id, state_id=state_id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found or access denied")
    
    try:
        return await ambulance_service.allocate_to_facility(db, ambulance_id=id, facility_id=allocation.facility_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/gps", response_model=Ambulance)
async def update_ambulance_gps(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    gps_in: GPSHistoryCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.AMBULANCE_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Update ambulance GPS position. (Ambulance Crew via App)
    """
    ambulance = await ambulance_service.update_gps(db, ambulance_id=id, obj_in=gps_in, state_id=state_id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found or access denied")
    return ambulance
