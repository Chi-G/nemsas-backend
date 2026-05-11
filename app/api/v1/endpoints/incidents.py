from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.incident import IncidentPaginatedResponse, IncidentResponse
from app.crud.incident import incident as crud_incident

router = APIRouter()

@router.get("/", response_model=IncidentPaginatedResponse)
async def read_incidents(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Fetch incidents matching operational view layout.
    """
    items, total = await crud_incident.get_multi_with_count(db, skip=skip, limit=limit)
    return {
        "success": True,
        "message": "Incident(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }

@router.get("/{id}", response_model=IncidentResponse)
async def read_incident(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Fetch a detailed Incident structure.
    """
    item = await crud_incident.get(db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    return {
        "success": True,
        "message": "Incident successfully fetched",
        "data": item
    }
