from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud.monitoring import monitoring as crud_monitoring
from app.schemas.common import ResponseBase
from app.schemas.monitoring import Monitoring as MonitoringSchema, MonitoringCreate
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[MonitoringSchema]])
async def read_monitoring(
    db: AsyncSession = Depends(deps.get_db),
    year: Optional[int] = None,
    month: Optional[int] = None,
    stateId: Optional[int] = None,
    remark: Optional[str] = None
) -> Any:
    """
    Returns monthly monitoring records matching the production payload.
    - Allows optional filtering by year, month, stateId, and remark.
    """
    items = await crud_monitoring.get_all(db, year=year, month=month, state_id=stateId, remark=remark)
    return {
        "success": True,
        "message": "Monthly data fetched successfully",
        "data": items
    }

@router.post("/", response_model=ResponseBase[MonitoringSchema])
async def create_monitoring(
    *,
    db: AsyncSession = Depends(deps.get_db),
    monitoring_in: MonitoringCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create a single monitoring record.
    """
    added_by = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.email
    db_obj = await crud_monitoring.create(db, obj_in=monitoring_in, added_by=added_by)
    return {
        "success": True,
        "message": "Monitoring record created successfully",
        "data": db_obj
    }

@router.post("/batch", response_model=ResponseBase[List[MonitoringSchema]])
async def create_monitoring_batch(
    *,
    db: AsyncSession = Depends(deps.get_db),
    monitoring_list: List[MonitoringCreate],
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create multiple monitoring records in batch.
    """
    added_by = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.email
    db_objs = await crud_monitoring.create_batch(db, obj_list=monitoring_list, added_by=added_by)
    return {
        "success": True,
        "message": f"Successfully created {len(db_objs)} monitoring records",
        "data": db_objs
    }

