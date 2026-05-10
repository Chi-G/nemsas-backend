from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.ward import Ward, WardCreate
from app.schemas.common import ResponseBase
from app.crud.ward import ward_crud

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[Ward]])
async def read_wards(
    db: AsyncSession = Depends(deps.get_db),
    lga_id: int = Query(None, alias="lgaId")
):
    if lga_id:
        wards = await ward_crud.get_by_lga(db, lga_id=lga_id)
    else:
        wards = await ward_crud.get_all(db)
        
    return {
        "success": True,
        "message": "Ward(s) successfully fetched",
        "data": wards
    }

@router.post("/", response_model=ResponseBase[Ward])
async def create_ward(
    *,
    db: AsyncSession = Depends(deps.get_db),
    ward_in: WardCreate,
):
    ward = await ward_crud.create(db, obj_in=ward_in)
    return {
        "success": True,
        "message": "Ward successfully created",
        "data": ward
    }
