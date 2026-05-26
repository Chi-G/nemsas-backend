from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any, cast
from app.api import deps
from app.schemas.incident import IncidentResponse, SingleIncidentResponse, IncidentSummary, Incident as IncidentSchema, IncidentCreate, IncidentUpdate
from app.crud.incident import incident_crud
from app.models.user import User

router = APIRouter()

@router.get("/last-event-status", response_model=Any)
async def get_last_event_status(
    incident_category_id: int = Query(..., alias="incidentCategoryId"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get the last event type status for a specific incident category.
    """
    last_status = await incident_crud.get_last_event_status(db, incident_category_id=incident_category_id)
    return {
        "success": True,
        "message": "Last event status successfully fetched",
        "data": {
            "lastEventStatus": last_status
        }
    }

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
    event_status_type: Optional[str] = Query(default=None, alias="eventStatusType"),
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
    - `eventStatusType`: Filter by event status type (alias: event_status_type).
    
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
        sort_by_state=sort_by_state,
        event_status_type=event_status_type
    )

    return {
        "success": True,
        "message": "Incidents successfully fetched",
        "data": incidents,
        "total": total
    }

@router.get("/ambulance", response_model=IncidentResponse)
async def read_ambulance_incidents(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieve incidents assigned to the current user's ambulance.
    """
    if current_user.ambulance_id is None:
        return {
            "success": True,
            "message": "No incidents found: you have no assigned ambulance",
            "data": [],
            "total": 0
        }

    incidents, total = await incident_crud.get_multi_by_ambulance(
        db,
        ambulance_id=cast(int, current_user.ambulance_id),
        skip=skip,
        limit=limit
    )

    return {
        "success": True,
        "message": "Ambulance incidents successfully fetched",
        "data": incidents,
        "total": total
    }

@router.get("/ambulance/{id}", response_model=SingleIncidentResponse)
async def read_ambulance_incident(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get a specific incident assigned to the current user's ambulance.
    """
    if current_user.ambulance_id is None:
        raise HTTPException(status_code=403, detail="User has no assigned ambulance")
    
    incident = await incident_crud.get(db, id=id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if incident.ambulance_id != current_user.ambulance_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this incident")

    return {
        "success": True,
        "message": "Incident details successfully fetched",
        "data": incident
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

    # Check if assigned ambulance is busy
    if incident_in.ambulance_id:
        from app.models.incident import Incident
        from sqlalchemy import select
        busy_check = await db.execute(
            select(Incident.id)
            .filter(Incident.ambulance_id == incident_in.ambulance_id)
            .filter(Incident.event_status_type == "Patient Picked Up")
            .limit(1)
        )
        if busy_check.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Assigned ambulance is currently busy with another patient"
            )

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

@router.patch("/{id}", response_model=Any)
async def update_incident(
    id: int,
    *,
    db: AsyncSession = Depends(deps.get_db),
    incident_in: IncidentUpdate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update an existing incident.
    """
    incident = await incident_crud.get(db, id=id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Permission check (simplified for now, usually restricted roles can only update their own state)
    restricted_roles = {"STATEVIEWER", "ADMINSEMSASUSER", "SEMSASDISPATCH", "SEMSASPIUUSER", "SEMSASUSER"}
    if current_user.user_type in restricted_roles and current_user.state_id != incident.state_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this incident")

    # Validation: Ambulance busy check
    target_ambulance_id = incident_in.ambulance_id if incident_in.ambulance_id is not None else incident.ambulance_id

    # 1. If assigning a new/different ambulance
    if incident_in.ambulance_id is not None and incident_in.ambulance_id != incident.ambulance_id:
        from app.models.incident import Incident
        from sqlalchemy import select
        busy_check = await db.execute(
            select(Incident.id)
            .filter(Incident.ambulance_id == incident_in.ambulance_id)
            .filter(Incident.event_status_type == "Patient Picked Up")
            .limit(1)
        )
        if busy_check.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Assigned ambulance is currently busy with another patient"
            )

    # 2. If setting event_status_type to "Patient Picked Up"
    if (
        (incident_in.event_status_type == "Patient Picked Up") or
        (incident.event_status_type == "Patient Picked Up" and incident_in.ambulance_id is not None and incident_in.ambulance_id != incident.ambulance_id)
    ):
        if target_ambulance_id:
            from app.models.incident import Incident
            from sqlalchemy import select
            busy_check = await db.execute(
                select(Incident.id)
                .filter(Incident.id != incident.id)
                .filter(Incident.ambulance_id == target_ambulance_id)
                .filter(Incident.event_status_type == "Patient Picked Up")
                .limit(1)
            )
            if busy_check.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail="Ambulance is already busy with another picked up patient"
                )

    updated_incident = await incident_crud.update(db, db_obj=incident, obj_in=incident_in)
    
    return {
        "success": True,
        "message": "Incident successfully updated",
        "data": IncidentSchema.model_validate(updated_incident)
    }
