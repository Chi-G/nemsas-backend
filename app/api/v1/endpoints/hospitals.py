from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.hospital import HospitalResponse, Hospital as HospitalSchema, HospitalCreate, HospitalUpdate
from app.crud.hospital import hospital_crud
from app.models.user import User
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy.future import select
from app.partners.models import PartnerUser
from sqlalchemy import func
from app.schemas.status_update import HospitalStatusUpdate
from app.core.email import send_approval_email

router = APIRouter()


@router.get("/", response_model=HospitalResponse)
async def read_hospitals(
    db: AsyncSession = Depends(deps.get_db),
    name: Optional[str] = None,
    stateId: Optional[int] = None,
    days: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve hospitals with filtering (SUPERADMINISTRATOR sees all, ADMINSEMSASUSER only their state).
    """
    effective_state_id = stateId
    if current_user.user_type in ["ADMINSEMSASUSER", "STATEVIEWER"]:
        effective_state_id = current_user.state_id
    
    hospitals, total = await hospital_crud.get_multi_with_count(
        db, 
        name=name,
        state_id=effective_state_id,
        days=days,
        status="approved"
    )
    from app.schemas.hospital import HospitalSummary
    return {
        "success": True,
        "message": "Hospital(s) successfully fetched",
        "data": [HospitalSummary.model_validate(h) for h in hospitals],
        "totalCount": total,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }
    

@router.get("/partner/stats")
async def get_partner_hospital_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """
    Get hospital statistics for the current partner (showing all hospitals).
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})

    from app.models.hospital import Hospital
    
    query = select(Hospital.status, func.count(Hospital.id)).group_by(Hospital.status)
    res = await db.execute(query)
    counts = res.all()
    
    stats = {"total": 0, "pending": 0, "approved": 0, "rejected": 0}
    for status_val, count in counts:
        stats["total"] += count
        if status_val in stats:
            stats[status_val] += count
            
    return {
        "success": True,
        "message": "Stats fetched successfully",
        "data": stats,
        "totalCount": 1
    }

@router.get("/partner", response_model=HospitalResponse)
async def read_partner_hospitals(
    db: AsyncSession = Depends(deps.get_db),
    name: Optional[str] = None,
    stateId: Optional[int] = None,
    days: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
) -> Any:
    """
    Retrieve hospitals for the partner dashboard (sees all).
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})

    hospitals, total = await hospital_crud.get_multi_with_count(
        db, 
        name=name,
        state_id=stateId,
        days=days,
        status=status,
        skip=skip,
        limit=limit
    )
    from app.schemas.hospital import HospitalSummary
    return {
        "success": True,
        "message": "Hospital(s) successfully fetched",
        "data": [HospitalSummary.model_validate(h) for h in hospitals],
        "totalCount": total,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.post("/partner", response_model=HospitalResponse)
async def create_partner_hospital(
    *,
    db: AsyncSession = Depends(deps.get_db),
    hospital_in: HospitalCreate,
    current_partner: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """
    Create a new hospital by a partner. Status will be pending.
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})
        
    hospital_in.added_by = current_partner.id
    hospital_in.status = "pending"
    if not hospital_in.date_added:
        hospital_in.date_added = datetime.now()
        
    try:
        new_hospital = await hospital_crud.create(db, obj_in=hospital_in)
        new_hospital = await hospital_crud.get(db, id=new_hospital.id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Hospital creation failed",
                "error": str(e)
            }
        )
        
    return {
        "success": True,
        "message": "Partner hospital successfully created",
        "data": new_hospital,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.post("/", response_model=HospitalResponse)
async def create_hospital(
    *,
    db: AsyncSession = Depends(deps.get_db),
    hospital_in: HospitalCreate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
) -> Any:
    """
    Create a new hospital.
    """
    if not hospital_in.date_added:
        hospital_in.date_added = datetime.now()
        
    try:
        new_hospital = await hospital_crud.create(db, obj_in=hospital_in)
        # Fetch the newly created hospital with relationships loaded
        new_hospital = await hospital_crud.get(db, id=new_hospital.id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Hospital creation failed",
                "error": str(e)
            }
        )
        
    return {
        "success": True,
        "message": "Hospital successfully created",
        "data": new_hospital,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }


@router.get("/{id}", response_model=HospitalResponse)
async def read_hospital(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get hospital by ID.
    """
    hospital = await hospital_crud.get(db, id=id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
        
    return {
        "success": True,
        "message": "Hospital successfully fetched",
        "data": hospital,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/state/{state_id}", response_model=HospitalResponse)
async def read_hospitals_by_state(
    state_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get hospitals by state ID.
    """
    hospitals = await hospital_crud.get_by_state(db, state_id=state_id)
    return {
        "success": True,
        "message": "Hospital(s) successfully fetched for state",
        "data": hospitals,
        "totalCount": len(hospitals),
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.patch("/{id}", response_model=HospitalResponse, summary="Edit Hospital")
async def update_hospital(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    hospital_in: HospitalUpdate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
) -> Any:
    """
    Update a hospital.
    - SUPERADMINISTRATOR can update any hospital.
    - ADMINSEMSASUSER can only update hospitals in their own state.
    """
    hospital_obj = await hospital_crud.get(db, id=id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")
        
    # Enforce state restriction for state admins
    if current_user.user_type == "ADMINSEMSASUSER":
        if current_user.state_id != hospital_obj.state_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to edit hospitals from other states"
            )
        # Enforce state admin cannot change hospital state to another state
        if hospital_in.state_id is not None and hospital_in.state_id != current_user.state_id:
            raise HTTPException(
                status_code=403,
                detail=f"You can only assign hospitals to your own state (ID: {current_user.state_id})"
            )
            
    updated_hospital = await hospital_crud.update(db, db_obj=hospital_obj, obj_in=hospital_in)
    return {
        "success": True,
        "message": "Hospital successfully updated",
        "data": updated_hospital,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.patch("/{id}/status", response_model=HospitalResponse)
async def update_hospital_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    status_update: HospitalStatusUpdate,
    current_user: Any = Depends(deps.PermissionCheckerAny(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
) -> Any:
    """
    Update the status of a hospital.
    Sends an email to the partner user who added the hospital if approved.
    """
    hospital_obj = await hospital_crud.get(db, id=id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")
        
    if current_user.user_type == "ADMINSEMSASUSER" and current_user.state_id != hospital_obj.state_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to edit hospitals from other states"
        )
        
    old_status = hospital_obj.status
    hospital_obj.status = status_update.status
    db.add(hospital_obj)
    await db.commit()
    await db.refresh(hospital_obj)
    
    # Send email if status is changed to approved
    if status_update.status == "approved" and old_status != "approved" and hospital_obj.added_by:
        # Fetch partner user
        partner_result = await db.execute(
            select(PartnerUser).where(PartnerUser.id == hospital_obj.added_by)
        )
        partner = partner_result.scalar_one_or_none()
        if partner and partner.email:
            send_approval_email(
                to_email=partner.email,
                name=partner.first_name,
                entity_type="Hospital", 
                entity_name=hospital_obj.name 
            )

    return {
        "success": True,
        "message": f"Hospital status successfully updated to {status_update.status}",
        "data": hospital_obj,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/{id}/patients", response_model=Any)
async def read_hospital_patients(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all patients assigned to a specific ETC.
    """
    from app.models.patient import Patient
    from sqlalchemy.future import select
    from app.schemas.patient import Patient as PatientSchema
    
    stmt = select(Patient).where(Patient.etc_id == id)
    result = await db.execute(stmt)
    patients = list(result.scalars().all())
    
    return {
        "success": True,
        "message": "Patients successfully fetched for ETC",
        "data": [PatientSchema.model_validate(p) for p in patients],
        "totalCount": len(patients)
    }

