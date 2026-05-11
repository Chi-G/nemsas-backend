from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.run_sheet import RunSheetPaginatedResponse
from app.crud.run_sheet import run_sheet as crud_run_sheet

router = APIRouter()

@router.get("/", response_model=RunSheetPaginatedResponse)
async def read_runsheets(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    items, total = await crud_run_sheet.get_multi_with_count(db, skip=skip, limit=limit)
    return {
        "success": True,
        "message": "Runsheet(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }
