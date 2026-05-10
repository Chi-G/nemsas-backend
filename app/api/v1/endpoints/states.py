from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.state import State, StateCreate
from app.schemas.common import ResponseBase
from app.crud.state import state_crud

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[State]])
async def read_states(
    db: AsyncSession = Depends(deps.get_db)
):
    states = await state_crud.get_all(db)
    return {
        "success": True,
        "message": "State(s) successfully fetched",
        "data": states
    }

@router.post("/", response_model=ResponseBase[State])
async def create_state(
    *,
    db: AsyncSession = Depends(deps.get_db),
    state_in: StateCreate,
):
    state = await state_crud.create(db, obj_in=state_in)
    return {
        "success": True,
        "message": "State successfully created",
        "data": state
    }
