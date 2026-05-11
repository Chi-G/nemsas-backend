from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.monitoring import Monitoring
from app.crud.monitoring import monitoring as crud_monitoring

router = APIRouter()

@router.get("/", response_model=List[Monitoring])
async def read_monitoring(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Returns top-level array for analytics grids.
    """
    return await crud_monitoring.get_all(db)
