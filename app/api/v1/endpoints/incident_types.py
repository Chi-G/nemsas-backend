from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.models.user import User
from app.schemas.incident_type import IncidentTypeResponse, IncidentTypeCreate, IncidentTypeUpdate
from app.crud.incident_type import incident_type_crud

router = APIRouter()

@router.get("/", response_model=IncidentTypeResponse)
async def read_incident_types(
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Retrieve all incident types.
    """
    types, total = await incident_type_crud.get_multi_with_count(db)
    from app.crud.incident import incident_crud
    for t in types:
        t.last_event_status = await incident_crud.get_last_event_status(db, incident_category_id=t.id)
    return {
        "success": True,
        "message": "Incident Type(s) successfully fetched",
        "data": types,
        "total_count": total
    }

@router.post("/", response_model=IncidentTypeResponse)
async def create_incident_type(
    obj_in: IncidentTypeCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
):
    """
    Create a new incident type.
    """
    new_type = await incident_type_crud.create(db, obj_in=obj_in)
    return {
        "success": True,
        "message": "Incident Type successfully created",
        "data": [new_type],
        "total_count": 1
    }

@router.put("/{id}", response_model=IncidentTypeResponse)
async def update_incident_type(
    id: int,
    obj_in: IncidentTypeUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
):
    """
    Update an existing incident type.
    """
    db_obj = await incident_type_crud.get(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Incident type not found")
    
    updated_type = await incident_type_crud.update(db, db_obj=db_obj, obj_in=obj_in)
    return {
        "success": True,
        "message": "Incident Type successfully updated",
        "data": [updated_type],
        "total_count": 1
    }
