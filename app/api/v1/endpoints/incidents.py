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
    state: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieve incidents with filtering and pagination.
    SuperAdmin can see all, others only their state.
    """
    effective_state_filter = None
    
    # Apply role-based filtering
    if current_user.user_type != "SUPERADMINISTRATOR":
        if current_user.state:
            effective_state_filter = current_user.state.name
        else:
            # If user has no state assigned and is not superadmin, they see nothing
            return {
                "success": True,
                "message": "No incidents found for your assigned state",
                "data": [],
                "total": 0
            }
    else:
        # SuperAdmin can filter by query param 'state' if provided
        effective_state_filter = state

    incidents, total = await incident_crud.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        triage=triage,
        state_name_filter=effective_state_filter
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
    Get incident by ID with full details (including patients).
    """
    incident = await incident_crud.get(db, id=id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Optional: Add permission check for individual incident access
    if current_user.user_type != "SUPERADMINISTRATOR":
        if current_user.state and incident.state_name:
            if current_user.state.name.lower() not in incident.state_name.lower():
                raise HTTPException(status_code=403, detail="Not authorized to access this incident")

    return incident
