from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.hospital import HospitalResponse, Hospital as HospitalSchema, HospitalCreate
from app.crud.hospital import hospital_crud
from app.models.user import User
from datetime import datetime
from typing import Any, List, Optional

router = APIRouter()


@router.get("/", response_model=HospitalResponse)
async def read_hospitals(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    stateId: Optional[int] = None,
    days: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve hospitals with filtering (SUPERADMINISTRATOR sees all, ADMINSEMSASUSER only their state).
    """
    effective_state_id = stateId
    if current_user.user_type == "ADMINSEMSASUSER":
        effective_state_id = current_user.state_id
    
    hospitals, total = await hospital_crud.get_multi_with_count(
        db, 
        skip=skip, 
        limit=limit,
        name=name,
        state_id=effective_state_id,
        days=days
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
