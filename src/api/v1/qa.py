from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.incident import QAFinding, QAFindingCreate
from src.services.qa import qa_service
from src.db.models.user import User
from src.core.rbac import Permission as PermissionEnum

router = APIRouter()

@router.post("/", response_model=QAFinding)
async def create_qa_finding(
    *,
    db: AsyncSession = Depends(get_db),
    finding_in: QAFindingCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.QA_ASSESS])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Create a new QA finding for an incident. (QA Officers, Admins)
    """
    try:
        return await qa_service.create_finding(
            db, obj_in=finding_in, officer_id=current_user.id, state_id=state_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/incident/{incident_id}", response_model=List[QAFinding])
async def read_incident_findings(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.QA_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get all QA findings for a given incident.
    """
    return await qa_service.get_findings_by_incident(db, incident_id=incident_id, state_id=state_id)
