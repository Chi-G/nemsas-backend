from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.ambulance import Ambulance, Dispatch
from src.services.dispatch import dispatch_service
from src.db.models.user import User

router = APIRouter()

@router.get("/nearest", response_model=List[Ambulance])
async def get_nearest_ambulances(
    *,
    db: AsyncSession = Depends(get_db),
    lat: float,
    lon: float,
    limit: int = 5,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get nearest available ambulances to a location. (Dispatchers, Admins)
    """
    return await dispatch_service.get_nearest_ambulances(db, latitude=lat, longitude=lon, limit=limit)

@router.post("/assign", response_model=List[Dispatch])
async def assign_ambulances(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    ambulance_ids: List[int],
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Assign one or more ambulances to an incident. (Dispatchers, Admins)
    """
    try:
        return await dispatch_service.assign_ambulances(
            db, incident_id=incident_id, ambulance_ids=ambulance_ids, current_user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
