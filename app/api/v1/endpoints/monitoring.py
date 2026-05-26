from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud.monitoring import monitoring as crud_monitoring
from app.schemas.common import ResponseBase
from app.schemas.monitoring import Monitoring as MonitoringSchema

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[MonitoringSchema]])
async def read_monitoring(
    db: AsyncSession = Depends(deps.get_db),
    year: Optional[int] = None,
    month: Optional[int] = None,
    stateId: Optional[int] = None
) -> Any:
    """
    Returns monthly monitoring records matching the production payload.
    - Allows optional filtering by year, month, and stateId.
    """
    items = await crud_monitoring.get_all(db, year=year, month=month, state_id=stateId)
    return {
        "success": True,
        "message": "Monthly data fetched successfully",
        "data": items
    }

