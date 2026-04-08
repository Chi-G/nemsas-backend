from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.ambulance import Ambulance, AmbulanceCreate, AmbulanceUpdate, GPSHistoryCreate
from src.services.ambulance import ambulance_service
from src.db.models.user import User

router = APIRouter()

@router.post("/", response_model=Ambulance)
async def create_ambulance(
    *,
    db: AsyncSession = Depends(get_db),
    ambulance_in: AmbulanceCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Register a new ambulance. (Admins, ETPs)
    """
    return await ambulance_service.create(db, obj_in=ambulance_in)

@router.get("/{id}", response_model=Ambulance)
async def read_ambulance(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get ambulance by ID.
    """
    ambulance = await ambulance_service.get_by_id(db, ambulance_id=id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    return ambulance

@router.post("/{id}/gps", response_model=Ambulance)
async def update_ambulance_gps(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    gps_in: GPSHistoryCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update ambulance GPS position. (Ambulance Crew via App)
    """
    return await ambulance_service.update_gps(db, ambulance_id=id, obj_in=gps_in)

@router.patch("/{id}/status", response_model=Ambulance)
async def update_ambulance_status(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    status_in: str, # Should be one of AmbulanceStatus
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update ambulance status. (Admins, Dispatchers)
    """
    ambulance = await ambulance_service.get_by_id(db, ambulance_id=id)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    return await ambulance_service.update_status(db, db_obj=ambulance, new_status=status_in)
