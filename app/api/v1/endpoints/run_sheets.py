from typing import Any, Optional, cast
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.run_sheet import RunSheetPaginatedResponse
from app.crud.run_sheet import run_sheet as crud_run_sheet
from app.models.user import User
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=RunSheetPaginatedResponse)
async def read_runsheets(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    state_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get list of runsheets matching the authenticated user's permissions and scope.
    - SUPERADMINISTRATOR & NEMSASADMIN can list globally and filter by state_id.
    - SEMSAS users list runsheets strictly within their own state.
    - AMBULANCEUSER list runsheets strictly matching their ambulance_id.
    - Other staff (medic/hospice/etc.) list runsheets matching their medic_user_id.
    """
    effective_medic_user_id = None
    effective_ambulance_id = None
    effective_state_id = None
    
    role = getattr(current_user, "user_type", "")
    
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN"]:
        effective_state_id = state_id
    elif role in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        effective_state_id = cast(Optional[int], current_user.state_id)
    elif role == "AMBULANCEUSER":
        effective_ambulance_id = cast(Optional[int], current_user.ambulance_id)
    else:
        effective_medic_user_id = cast(Optional[UUID], current_user.id)

    items, total = await crud_run_sheet.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        medic_user_id=effective_medic_user_id,
        ambulance_id=effective_ambulance_id,
        state_id=effective_state_id
    )
    return {
        "success": True,
        "message": "Runsheet(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }
