from typing import Any, Optional, cast
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.run_sheet import RunSheetPaginatedResponse, RunSheetCreate
from app.crud.run_sheet import run_sheet as crud_run_sheet
from app.models.user import User
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=RunSheetPaginatedResponse)
async def read_runsheets(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    state_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get list of runsheets matching the authenticated user's permissions and scope.
    - SUPERADMINISTRATOR & NEMSASADMIN can list globally and filter by state_id.
    - SEMSAS users list runsheets strictly within their own state.
    - AMBULANCEUSER list runsheets strictly matching their ambulance_id.
    - Other staff (medic/hospice/etc.) list runsheets matching their medic_user_id.
    """
    effective_medic_user_id = None
    effective_ambulance_id = None
    effective_state_id = None
    
    role = getattr(current_user, "user_type", "")
    
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN"]:
        effective_state_id = state_id
    elif role in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        effective_state_id = cast(Optional[int], current_user.state_id)
    elif role == "AMBULANCEUSER":
        effective_ambulance_id = cast(Optional[int], current_user.ambulance_id)
    else:
        effective_medic_user_id = cast(Optional[UUID], current_user.id)

    items, total = await crud_run_sheet.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        medic_user_id=effective_medic_user_id,
        ambulance_id=effective_ambulance_id,
        state_id=effective_state_id
    )
    return {
        "success": True,
        "message": "Runsheet(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }

@router.post("/")
async def create_runsheet(
    *,
    db: AsyncSession = Depends(deps.get_db),
    run_sheet_in: RunSheetCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create a new runsheet.
    Only AMBULANCEUSER can access this endpoint.
    The ambulanceId is automatically set to the signed-in user's ambulance.
    """
    if getattr(current_user, "user_type", "") != "AMBULANCEUSER":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only an AMBULANCEUSER can create a runsheet"
        )
    
    if current_user.ambulance_id is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400, 
            detail="User does not have an assigned ambulance"
        )
        
    # Override ambulanceId from current user
    run_sheet_in.ambulance_id = current_user.ambulance_id
    
    # Calculate status based on signatures
    status = "Draft"
    if run_sheet_in.medic_user_id and run_sheet_in.hospice_user_id:
        status = "Fully Co-Signed"
    elif run_sheet_in.medic_user_id:
        status = "Awaiting ETC Co-Signature"
        
    obj_in_data = run_sheet_in.model_dump(exclude_unset=True, by_alias=False)
    obj_in_data["status"] = status
    
    from app.models.run_sheet import RunSheet
    db_obj = RunSheet(**obj_in_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    # Reload with relationships
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    stmt = select(RunSheet).options(
        selectinload(RunSheet.medic_user).selectinload(User.state),
        selectinload(RunSheet.medic_user).selectinload(User.lga),
        selectinload(RunSheet.medic_user).selectinload(User.ward),
        selectinload(RunSheet.incident),
        selectinload(RunSheet.emergency_treatment_center),
    ).where(RunSheet.id == db_obj.id)
    result = await db.execute(stmt)
    new_runsheet = result.scalar_one()
    
    from app.schemas.run_sheet import RunSheet as RunSheetResponseSchema
    
    return {
        "success": True,
        "message": "Runsheet successfully created",
        "data": RunSheetResponseSchema.model_validate(new_runsheet)
    }

from app.schemas.run_sheet import SingleRunSheetAmbulanceResponse, RunSheetAmbulancePaginatedResponse

@router.get("/ambulance", response_model=RunSheetAmbulancePaginatedResponse)
async def read_ambulance_runsheets(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve runsheets assigned to the current user's ambulance.
    Only accessible to AMBULANCEUSER.
    """
    if getattr(current_user, "user_type", "") != "AMBULANCEUSER":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only an AMBULANCEUSER can view ambulance runsheets"
        )

    if current_user.ambulance_id is None:
        return {
            "success": True,
            "message": "No runsheets found: you have no assigned ambulance",
            "data": {"items": []},
            "totalCount": 0
        }

    items, total = await crud_run_sheet.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        ambulance_id=int(current_user.ambulance_id),
        exclude_null_incident=True,
        load_medic_user=False
    )

    return {
        "success": True,
        "message": "Ambulance runsheets successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }

@router.get("/ambulance/{id}", response_model=SingleRunSheetAmbulanceResponse)
async def read_ambulance_runsheet(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a specific runsheet details assigned to the current user's ambulance.
    """
    if getattr(current_user, "user_type", "") != "AMBULANCEUSER":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only an AMBULANCEUSER can view ambulance runsheets"
        )
        
    if current_user.ambulance_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="User has no assigned ambulance")
    
    run_sheet_record = await crud_run_sheet.get(db, id=id, load_medic_user=False)
    if not run_sheet_record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Runsheet not found")
    
    if run_sheet_record.ambulance_id != current_user.ambulance_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized to access this runsheet")

    return {
        "success": True,
        "message": "Runsheet details successfully fetched",
        "data": run_sheet_record
    }
