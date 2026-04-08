from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.base import get_db
from src.schemas.reference import State, LGA, Drug
from src.db.models.reference import State as DBState, LGA as DBLGA, Drug as DBDrug

router = APIRouter()

@router.get("/states", response_model=List[State])
async def read_states(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all states.
    """
    result = await db.execute(select(DBState).order_by(DBState.name))
    return result.scalars().all()

@router.get("/states/{state_id}/lgas", response_model=List[LGA])
async def read_state_lgas(
    state_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all LGAs for a state.
    """
    result = await db.execute(select(DBLGA).where(DBLGA.state_id == state_id).order_by(DBLGA.name))
    return result.scalars().all()

@router.get("/drugs", response_model=List[Drug])
async def read_drugs(
    db: AsyncSession = Depends(get_db),
    query: str = None,
) -> Any:
    """
    Get NHIA approved drugs.
    """
    stmt = select(DBDrug).where(DBDrug.is_active == True)
    if query:
        stmt = stmt.where(DBDrug.name.ilike(f"%{query}%"))
    result = await db.execute(stmt.order_by(DBDrug.name))
    return result.scalars().all()
