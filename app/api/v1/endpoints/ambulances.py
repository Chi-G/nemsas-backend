from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api import deps
from app.schemas.ambulance import AmbulanceResponse, AmbulanceCreate, AmbulanceUpdate
from app.crud.crud_ambulance import ambulance as ambulance_crud
from app.models.user import User
from app.models.partner import Partner
from app.partners.models import PartnerUser
import string
import random
from app.schemas.status_update import AmbulanceStatusUpdate
from app.core.email import send_approval_email

router = APIRouter()

@router.get("/", response_model=AmbulanceResponse)
async def read_ambulances(
    db: AsyncSession = Depends(deps.get_db),
    driverName: Optional[str] = None,
    name: Optional[str] = None,
    stateId: Optional[int] = None,
    typeId: Optional[int] = None,
    days: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve ambulances with filtering (SUPERADMINISTRATOR sees all, ADMINSEMSASUSER only their state).
    """
    effective_state_id = stateId
    if current_user.user_type in ["ADMINSEMSASUSER", "STATEVIEWER"]:
        effective_state_id = current_user.state_id

    ambulances, total_count = await ambulance_crud.get_multi_with_count(
        db, 
        driver_name=driverName,
        name=name,
        state_id=effective_state_id,
        ambulance_type_id=typeId,
        days=days,
        status="approved"
    )
    from app.schemas.ambulance import AmbulanceSummary
    return {
        "success": True,
        "message": "Ambulance(s) successfully fetched",
        "data": [AmbulanceSummary.model_validate(a) for a in ambulances],
        "totalCount": total_count,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/all", response_model=AmbulanceResponse)
async def read_all_ambulances(
    db: AsyncSession = Depends(deps.get_db),
    driverName: Optional[str] = None,
    name: Optional[str] = None,
    stateId: Optional[int] = None,
    typeId: Optional[int] = None,
    days: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve all ambulances with optional status filtering.
    """
    effective_state_id = stateId
    if current_user.user_type in ["ADMINSEMSASUSER", "STATEVIEWER"]:
        effective_state_id = current_user.state_id

    ambulances, total_count = await ambulance_crud.get_multi_with_count(
        db, 
        driver_name=driverName,
        name=name,
        state_id=effective_state_id,
        ambulance_type_id=typeId,
        days=days,
        status=status
    )
    from app.schemas.ambulance import AmbulanceSummary
    return {
        "success": True,
        "message": "Ambulance(s) successfully fetched",
        "data": [AmbulanceSummary.model_validate(a) for a in ambulances],
        "totalCount": total_count,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.post("/", response_model=AmbulanceResponse)
async def create_ambulance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    ambulance_in: AmbulanceCreate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
) -> Any:
    """
    Create a new ambulance.
    """
    if not ambulance_in.code:
        # Generate a random code like AMB-XXXXXX
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        ambulance_in.code = f"AMB-{random_str}"
        
    try:
        new_ambulance = await ambulance_crud.create(db, obj_in=ambulance_in)
    except Exception as e:
        # Check for unique constraint violation on code or name if any
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Ambulance creation failed",
                "error": str(e)
            }
        )
        
    return {
        "success": True,
        "message": "Ambulance successfully created",
        "data": new_ambulance,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.post("/partner", response_model=AmbulanceResponse)
async def create_partner_ambulance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    ambulance_in: AmbulanceCreate,
    current_partner: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """
    Create a new ambulance by a partner. Status will be pending.
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})

    ambulance_in.status = "pending"
    ambulance_in.added_by = current_partner.id

    if not ambulance_in.code:
        # Generate a random code like AMB-XXXXXX
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        ambulance_in.code = f"AMB-{random_str}"
        
    try:
        new_ambulance = await ambulance_crud.create(db, obj_in=ambulance_in)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Ambulance creation failed",
                "error": str(e)
            }
        )
        
    return {
        "success": True,
        "message": "Partner ambulance successfully created",
        "data": new_ambulance,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/partner/stats")
async def get_partner_ambulance_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """
    Get ambulance statistics for the current partner.
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})

    from sqlalchemy import func
    from app.models.ambulance import Ambulance
    
    query = select(Ambulance.status, func.count(Ambulance.id)).group_by(Ambulance.status)
    res = await db.execute(query)
    counts = res.all()
    
    stats = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "under_maintenance": 0, "out_of_service": 0}
    for status_val, count in counts:
        stats["total"] += count
        if not status_val:
            continue
            
        key = status_val.lower()
        if key in ["under maintenance", "under_maintainance", "under_maintenance"]:
            stats["under_maintenance"] += count
        elif key in ["out of service", "out_of_service"]:
            stats["out_of_service"] += count
        elif key in stats:
            stats[key] += count
            
    return {
        "success": True,
        "message": "Stats fetched successfully",
        "data": stats,
        "totalCount": 1
    }

@router.get("/partner", response_model=AmbulanceResponse)
async def read_partner_ambulances(
    db: AsyncSession = Depends(deps.get_db),
    driverName: Optional[str] = None,
    name: Optional[str] = None,
    stateId: Optional[int] = None,
    typeId: Optional[int] = None,
    days: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
) -> Any:
    """
    Retrieve ambulances added by the current partner.
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})

    ambulances, total_count = await ambulance_crud.get_multi_with_count(
        db, 
        driver_name=driverName,
        name=name,
        state_id=stateId,
        ambulance_type_id=typeId,
        days=days,
        status=status,
        skip=skip,
        limit=limit
    )
    from app.schemas.ambulance import AmbulanceSummary
    return {
        "success": True,
        "message": "Partner ambulance(s) successfully fetched",
        "data": [AmbulanceSummary.model_validate(a) for a in ambulances],
        "totalCount": total_count,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }
@router.get("/{id}", response_model=AmbulanceResponse)
async def read_ambulance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Get ambulance by ID.
    """
    ambulance = await ambulance_crud.get(db, id=id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    return {
        "success": True,
        "message": "Ambulance successfully fetched",
        "data": ambulance,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/state/{state_id}", response_model=AmbulanceResponse)
async def read_ambulances_by_state(
    state_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get ambulances by state ID.
    """
    ambulances = await ambulance_crud.get_by_state(db, state_id=state_id)
    return {
        "success": True,
        "message": "Ambulance(s) successfully fetched for state",
        "data": ambulances,
        "totalCount": len(ambulances),
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.patch("/{id}", response_model=AmbulanceResponse, summary="Edit Ambulance")
async def update_ambulance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    ambulance_in: AmbulanceUpdate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
) -> Any:
    """
    Update an ambulance.
    - SUPERADMINISTRATOR can update any ambulance.
    - ADMINSEMSASUSER can only update ambulances in their own state.
    """
    ambulance_obj = await ambulance_crud.get(db, id=id)
    if not ambulance_obj:
        raise HTTPException(status_code=404, detail="Ambulance not found")
        
    # Enforce state restriction for state admins
    if current_user.user_type == "ADMINSEMSASUSER":
        if current_user.state_id != ambulance_obj.state_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to edit ambulances from other states"
            )
        # Enforce state admin cannot change ambulance state to another state
        if ambulance_in.state_id is not None and ambulance_in.state_id != current_user.state_id:
            raise HTTPException(
                status_code=403,
                detail=f"You can only assign ambulances to your own state (ID: {current_user.state_id})"
            )
            
    updated_ambulance = await ambulance_crud.update(db, db_obj=ambulance_obj, obj_in=ambulance_in)
    return {
        "success": True,
        "message": "Ambulance successfully updated",
        "data": updated_ambulance,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.patch("/{id}/status", response_model=AmbulanceResponse)
async def update_ambulance_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    status_update: AmbulanceStatusUpdate,
    current_user: Any = Depends(deps.PermissionCheckerAny(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
) -> Any:
    """
    Update the status of an ambulance.
    Sends an email to the partner user who added the ambulance if approved.
    """
    ambulance_obj = await ambulance_crud.get(db, id=id)
    if not ambulance_obj:
        raise HTTPException(status_code=404, detail="Ambulance not found")
        
    if current_user.user_type == "ADMINSEMSASUSER" and current_user.state_id != ambulance_obj.state_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to edit ambulances from other states"
        )
        
    old_status = ambulance_obj.status
    ambulance_obj.status = status_update.status
    db.add(ambulance_obj)
    await db.commit()
    await db.refresh(ambulance_obj)
    
    # Send email if status is changed to approved
    if status_update.status == "approved" and old_status != "approved" and ambulance_obj.added_by:
        # Fetch partner user
        partner_result = await db.execute(
            select(PartnerUser).where(PartnerUser.id == ambulance_obj.added_by)
        ) 
        partner = partner_result.scalar_one_or_none()
        if partner and partner.email:
            send_approval_email(
                to_email=partner.email,
                name=partner.first_name,
                entity_type="Ambulance",
                entity_name=ambulance_obj.name
            )

    return {
        "success": True,
        "message": f"Ambulance status successfully updated to {status_update.status}",
        "data": ambulance_obj,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }
