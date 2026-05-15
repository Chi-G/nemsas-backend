from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.api import deps
from app.schemas.incident import IncidentResponse, IncidentSummary, Incident as IncidentSchema
from app.crud.incident import incident_crud
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=IncidentResponse)
async def read_incidents(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    triage: Optional[str] = None,
    state_id: Optional[int] = None,
    mass_casualty: Optional[bool] = None,
    sort_by_state: bool = False,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieve incidents with filtering and pagination.
    
    **Filtering:**
    - `search`: Search in serial number, caller name, or description.
    - `status`: Filter by incident status.
    - `triage`: Filter by triage category.
    - `state_id`: Filter by state ID (only for Global roles).
    - `mass_casualty`: Filter by mass casualty status (true/false).
    - `sort_by_state`: Sort results by state name (ascending).
    
    **Role-based Access:**
    - **Restricted Roles** (STATEVIEWER, ADMINSEMSASUSER, SEMSASDISPATCH, SEMSASPIUUSER, SEMSASUSER): 
      Automatically filtered by the user's assigned state.
    - **Global Roles** (NEMSASUSER, NATIONALVIEWER, SUPERADMINISTRATOR, NEMSASADMIN): 
      Can see incidents from all states and use the `state_id` filter.
    """
    restricted_roles = {"STATEVIEWER", "ADMINSEMSASUSER", "SEMSASDISPATCH", "SEMSASPIUUSER", "SEMSASUSER"}
    
    state_id_filter = None
    
    # Apply role-based filtering
    if current_user.user_type in restricted_roles:
        if current_user.state_id:
            state_id_filter = current_user.state_id
        else:
            # If user has no state assigned and is in a restricted role, they see nothing
            return {
                "success": True,
                "message": "No incidents found: you have no assigned state",
                "data": [],
                "total": 0
            }

    incidents, total = await incident_crud.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        triage=triage,
        state_id=state_id,
        state_id_filter=state_id_filter,
        mass_casualty=mass_casualty,
        sort_by_state=sort_by_state
    )

    return {
        "success": True,
        "message": "Incidents successfully fetched",
        "data": incidents,
        "total": total
    }

@router.get("/{id}", response_model=IncidentSchema)
async def read_incident(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get incident by ID with full details.
    """
    incident = await incident_crud.get(db, id=id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    restricted_roles = {"STATEVIEWER", "ADMINSEMSASUSER", "SEMSASDISPATCH", "SEMSASPIUUSER", "SEMSASUSER"}
    
    # Permission check for restricted roles
    if current_user.user_type in restricted_roles:
        if current_user.state_id != incident.state_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this incident")

    return incident
