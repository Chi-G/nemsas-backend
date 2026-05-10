from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List
from app.api import deps
from app.schemas.ambulance_type import AmbulanceTypeResponse, AmbulanceType as AmbulanceTypeSchema
from app.crud.ambulance_type import ambulance_type_crud
from app.models.ambulance_type import AmbulanceType

router = APIRouter()

@router.get("/", response_model=AmbulanceTypeResponse)
async def read_ambulance_types(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve ambulance types.
    """
    ambulance_types = await ambulance_type_crud.get_multi(db, skip=skip, limit=limit)
    
    # Get total count
    count_result = await db.execute(select(func.count()).select_from(AmbulanceType))
    total = count_result.scalar()

    return {
        "success": True,
        "message": "Ambulance Type(s) successfully fetched",
        "data": ambulance_types,
        "totalCount": total,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/{id}", response_model=AmbulanceTypeResponse)
async def read_ambulance_type(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get ambulance type by ID.
    """
    ambulance_type = await ambulance_type_crud.get(db, id=id)
    if not ambulance_type:
        raise HTTPException(status_code=404, detail="Ambulance type not found")
        
    return {
        "success": True,
        "message": "Ambulance Type successfully fetched",
        "data": ambulance_type,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }
