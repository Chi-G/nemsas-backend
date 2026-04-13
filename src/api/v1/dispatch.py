from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.ambulance import Ambulance, Dispatch, AmbulanceSearchResult
from src.services.dispatch import dispatch_service
from src.db.models.user import User
from src.core.rbac import Permission

router = APIRouter()

@router.get("/nearest", response_model=List[AmbulanceSearchResult])
async def get_nearest_ambulances(
    *,
    db: AsyncSession = Depends(get_db),
    lat: float,
    lon: float,
    limit: int = 5,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.DISPATCH_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get nearest available ambulances to a location. (Dispatchers, Admins)
    """
    return await dispatch_service.get_nearest_ambulances(
        db, latitude=lat, longitude=lon, limit=limit, state_id=state_id
    )

@router.post("/assign", response_model=List[Dispatch])
async def assign_ambulances(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    ambulance_ids: List[int],
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.DISPATCH_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Assign one or more ambulances to an incident. (Dispatchers, Admins)
    """
    try:
        return await dispatch_service.assign_ambulances(
            db, 
            incident_id=incident_id, 
            ambulance_ids=ambulance_ids, 
            current_user_id=current_user.id,
            state_id=state_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/accept", response_model=Dispatch)
async def accept_dispatch(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    # Normally we check if current_user belongs to the crew of this dispatch
) -> Any:
    """
    Accept an assigned dispatch. (Ambulance Crew)
    Triggers automatic creation of a Run Sheet.
    """
    try:
        return await dispatch_service.accept_dispatch(
            db, dispatch_id=id, user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
