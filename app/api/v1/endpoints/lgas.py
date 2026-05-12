from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.lga import LGA, LGACreate
from app.schemas.common import ResponseBase
from app.crud.lga import lga_crud

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[LGA]])
async def read_lgas(
    db: AsyncSession = Depends(deps.get_db),
    state_id: int = Query(None, alias="stateId")
):
    if state_id:
        lgas = await lga_crud.get_by_state(db, state_id=state_id)
    else:
        lgas = await lga_crud.get_all(db)
    
    return {
        "success": True,
        "message": "Lga(s) successfully fetched",
        "data": lgas
    }

@router.post("/", response_model=ResponseBase[LGA])
async def create_lga(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lga_in: LGACreate,
):
    lga = await lga_crud.create(db, obj_in=lga_in)
    return {
        "success": True,
        "message": "Lga successfully created",
        "data": lga
    }
