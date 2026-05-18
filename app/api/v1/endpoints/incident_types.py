from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.incident_type import IncidentTypeResponse
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
    return {
        "success": True,
        "message": "Incident Type(s) successfully fetched",
        "data": types,
        "total_count": total
    }
