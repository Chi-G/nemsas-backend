from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.services.me import me_service
from src.db.models.user import User

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
async def get_national_summary(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get national gap analysis and performance summary.
    """
    return await me_service.get_national_summary(db)

@router.get("/summary/state/{state_id}", response_model=Dict[str, Any])
async def get_state_summary(
    *,
    db: AsyncSession = Depends(get_db),
    state_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get state-level performance and gap analysis.
    """
    # If SEMSAS Admin, ensure they can only access their own state
    if current_user.state_id and current_user.state_id != state_id:
        raise HTTPException(status_code=403, detail="Access to other states restricted")
        
    return await me_service.get_state_summary(db, state_id=state_id)
