from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.hospital_type import HospitalTypeResponse, HospitalType as HospitalTypeSchema
from app.crud.hospital_type import hospital_type_crud

router = APIRouter()

@router.get("/", response_model=HospitalTypeResponse)
async def read_hospital_types(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve hospital types.
    """
    hospital_types = await hospital_type_crud.get_multi(db, skip=skip, limit=limit)
    
    # Simple count for hospital types (usually a small table)
    from sqlalchemy import func, select
    from app.models.hospital_type import HospitalType
    count_result = await db.execute(select(func.count()).select_from(HospitalType))
    total = count_result.scalar()

    return {
        "success": True,
        "message": "Hospital Type(s) successfully fetched",
        "data": hospital_types,
        "totalCount": total,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }

@router.get("/{id}", response_model=HospitalTypeResponse)
async def read_hospital_type(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get hospital type by ID.
    """
    hospital_type = await hospital_type_crud.get(db, id=id)
    if not hospital_type:
        raise HTTPException(status_code=404, detail="Hospital type not found")
        
    return {
        "success": True,
        "message": "Hospital Type successfully fetched",
        "data": hospital_type,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }
