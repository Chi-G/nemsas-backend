from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.api import deps
from app.schemas.incident import IncidentResponse, IncidentSummary
from app.crud.incident import incident_crud

router = APIRouter()

@router.get("/", response_model=IncidentResponse)
async def read_incidents(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    triage: Optional[str] = None,
    state: Optional[str] = None
):
    """
    Retrieve incidents with filtering and pagination.
    """
    incidents, total = await incident_crud.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        triage=triage,
        state=state
    )

    return {
        "success": True,
        "message": "Incidents successfully fetched",
        "data": incidents,
        "total": total
    }

@router.get("/{id}", response_model=IncidentSummary)
async def read_incident(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get incident by ID.
    """
    incident = await incident_crud.get(db, id=id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
