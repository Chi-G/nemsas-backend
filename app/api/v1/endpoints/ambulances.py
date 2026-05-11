from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.ambulance import AmbulanceResponse, AmbulanceCreate
from app.crud.crud_ambulance import ambulance as ambulance_crud
from app.models.user import User
import string
import random

router = APIRouter()

@router.get("/", response_model=AmbulanceResponse)
async def read_ambulances(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    driverName: Optional[str] = None,
    stateId: Optional[int] = None,
    days: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve ambulances with filtering (SUPERADMINISTRATOR sees all, ADMINSEMSASUSER only their state).
    """
    effective_state_id = stateId
    if current_user.user_type == "ADMINSEMSASUSER":
        effective_state_id = current_user.state_id

    ambulances, total_count = await ambulance_crud.get_multi_with_count(
        db, 
        skip=skip, 
        limit=limit,
        driver_name=driverName,
        state_id=effective_state_id,
        days=days
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
