from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any, cast
from app.api import deps
from app.schemas.incident import IncidentResponse, IncidentSummary, Incident as IncidentSchema, IncidentCreate
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
    incident_category_id: Optional[int] = None,
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
    - `incident_category_id`: Filter by incident category ID.
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
        if current_user.state_id is not None:
            state_id_filter = cast(int, current_user.state_id)
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
        incident_category_id=incident_category_id,
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

@router.post("/", response_model=Any)
async def create_incident(
    *,
    db: AsyncSession = Depends(deps.get_db),
    incident_in: IncidentCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new incident.
    
    Only **SEMSASDISPATCH** and **EMERGENCYTREATMENTUSER** are allowed to create incidents.
    """
    allowed_roles = {"SEMSASDISPATCH", "EMERGENCYTREATMENTUSER"}
    if current_user.user_type not in allowed_roles:
        raise HTTPException(
            status_code=403, 
            detail="Only SEMSASDISPATCH and EMERGENCYTREATMENTUSER can create incidents"
        )
    
    # If state_id is not provided in payload, use user's state_id
    if not incident_in.state_id and current_user.state_id is not None:
        incident_in.state_id = cast(int, current_user.state_id)

    # Resolve incident category name to ID if needed
    if not incident_in.incident_category_id and incident_in.incident_category:
        from app.models.incident_type import IncidentType
        from sqlalchemy import select
        category_result = await db.execute(
            select(IncidentType).filter(IncidentType.name.ilike(incident_in.incident_category))
        )
        category = category_result.scalars().first()
        if category:
            incident_in.incident_category_id = cast(int, category.id)

    new_incident = await incident_crud.create(db, obj_in=incident_in)
    
    # Broadcast incident via Websockets
    from app.services.notification_service import notification_service
    # Construct a payload, excluding complex objects
    incident_data = IncidentSchema.model_validate(new_incident).model_dump(mode="json")
    await notification_service.publish_incident(incident_data)
    
    return {
        "success": True,
        "message": "Incident successfully created",
        "data": incident_data
    }
