from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.incident import Incident, IncidentCreate, IncidentUpdate
from src.services.incident import incident_service
from src.db.models.user import User

router = APIRouter()

@router.post("/", response_model=Incident)
async def create_incident(
    *,
    db: AsyncSession = Depends(get_db),
    incident_in: IncidentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new incident. (Dispatchers, Admins, Public via App)
    """
    return await incident_service.create(db, obj_in=incident_in, creator_id=current_user.id)

@router.get("/{uuid}", response_model=Incident)
async def read_incident(
    *,
    db: AsyncSession = Depends(get_db),
    uuid: str,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get incident by UUID.
    """
    incident = await incident_service.get_by_uuid(db, uuid_str=uuid)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/{uuid}/status", response_model=Incident)
async def update_incident_status(
    *,
    db: AsyncSession = Depends(get_db),
    uuid: str,
    status_in: str, # Should be one of IncidentStatus
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update incident status.
    """
    incident = await incident_service.get_by_uuid(db, uuid_str=uuid)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Simple status transition logic - could be expanded to validate the workflow
    return await incident_service.update_status(
        db, db_obj=incident, new_status=status_in, changer_id=current_user.id
    )
