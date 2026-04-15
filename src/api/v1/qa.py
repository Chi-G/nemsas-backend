from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.qa import QAFilter, QAIncidentSummary, QAFindingRead, QAFindingCreate
from src.services.qa import qa_service
from src.db.models.user import User
from src.core.rbac import Permission as PermissionEnum
from datetime import datetime

router = APIRouter()

@router.get("/incidents", response_model=List[QAIncidentSummary])
async def read_qa_incidents(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    state_id: Optional[int] = Query(None),
    lga_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    ambulance_id: Optional[int] = Query(None),
    compliance_rating: Optional[str] = Query(None),
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.QA_READ])),
    state_scope: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Retrieve completed/closed incidents for QA review. (QA Officers, Admins)
    """
    filters = QAFilter(
        state_id=state_id,
        lga_id=lga_id,
        date_from=date_from,
        date_to=date_to,
        ambulance_id=ambulance_id,
        compliance_rating=compliance_rating
    )
    return await qa_service.get_qa_incidents_paginated(
        db, filters=filters, skip=skip, limit=limit, state_id=state_scope
    )

@router.post("/", response_model=QAFindingRead)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/incident/{incident_id}", response_model=List[QAFindingRead])
async def read_incident_findings(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.QA_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get the history of QA findings for a given incident.
    """
    return await qa_service.get_findings_by_incident(db, incident_id=incident_id, state_id=state_id)
