from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.incident import Incident, IncidentCreate, IncidentUpdate
from src.services.incident import incident_service
from src.db.models.user import User
from src.core.rbac import Permission

router = APIRouter()

@router.post("/", response_model=Incident)
async def create_incident(
    *,
    db: AsyncSession = Depends(get_db),
    incident_in: IncidentCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_CREATE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Create a new incident (Criterion 56). (Dispatchers, Admins, Public via App)
    """
    # If SEMSAS Admin, ensure they only create for their state
    if state_id and incident_in.state_id != state_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SEMSAS Admins can only create incidents in their assigned state"
        )
    return await incident_service.create(db, obj_in=incident_in, creator_id=current_user.id)

@router.get("/", response_model=List[Incident])
async def read_incidents(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    emergency_type: Optional[str] = None,
    lga_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Retrieve incidents. Automatically scoped to state for SEMSAS Admins.
    """
    return await incident_service.list(
        db, 
        skip=skip, 
        limit=limit, 
        status=status, 
        state_id=state_id, 
        lga_id=lga_id, 
        emergency_type=emergency_type
    )

@router.get("/location-search", response_model=List[dict])
async def search_locations(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_CREATE, Permission.INCIDENT_READ])),
) -> Any:
    """
    Criterion 62: Search health facilities and LGAs for incident location confirmation.
    """
    return await incident_service.search_locations(db, query=query)

@router.get("/{uuid}", response_model=Incident)
async def read_incident(
    *,
    db: AsyncSession = Depends(get_db),
    uuid: str,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get full incident record including status history (Criterion 66).
    """
    incident = await incident_service.get_full_incident(db, uuid_str=uuid, state_id=state_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found or access denied")
    return incident

@router.patch("/{uuid}/status", response_model=Incident)
async def update_incident_status(
    *,
    db: AsyncSession = Depends(get_db),
    uuid: str,
    status_in: str,
    notes: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Update incident status with strict workflow validation (Criterion 63).
    """
    incident = await incident_service.get_by_uuid(db, uuid_str=uuid, state_id=state_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found or access denied")
    
    return await incident_service.update_status(
        db, db_obj=incident, new_status=status_in, changer_id=current_user.id, notes=notes
    )

@router.post("/{uuid}/close", response_model=Incident)
async def close_incident(
    *,
    db: AsyncSession = Depends(get_db),
    uuid: str,
    notes: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_CLOSE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Criterion 67: Close incident. Only possible if status is 'Completed'.
    """
    incident = await incident_service.get_by_uuid(db, uuid_str=uuid, state_id=state_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found or access denied")
    
    from src.db.models.incident import IncidentStatus
    if incident.status != IncidentStatus.COMPLETED:
        # Special case: allow direct close for False Alarms if it's currently 'Created'
        if incident.status != IncidentStatus.CREATED:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot close incident from current status: {incident.status}. Must be 'Completed' or 'Created'."
            )
            
    return await incident_service.update_status(
        db, db_obj=incident, new_status=IncidentStatus.CLOSED, changer_id=current_user.id, notes=notes
    )
