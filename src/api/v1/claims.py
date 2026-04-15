from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.api import deps
from src.db.base import get_db
from src.schemas.claim import Claim, ClaimCreate, ClaimUpdate, RunSheet, RunSheetUpdate, ETCIntake, ETCIntakeCreate, ClaimFilter, ClaimPair, ClaimDetail
from src.services.claim import claim_service
from src.db.models.user import User
from src.db.models.claim import ClaimStatus, ClaimType
from src.core.rbac import Permission as PermissionEnum
from fastapi.responses import Response

router = APIRouter()

@router.get("/run-sheet/{incident_id}", response_model=RunSheet)
async def read_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.CLAIM_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get run sheet by incident ID.
    """
    run_sheet = await claim_service.get_run_sheet(db, incident_id=incident_id, state_id=state_id)
    if not run_sheet:
        raise HTTPException(status_code=404, detail="Run sheet not found")
    return run_sheet

@router.post("/run-sheet/{incident_id}", response_model=RunSheet)
async def create_or_update_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    run_sheet_in: RunSheetUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.RUNSHEET_WRITE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Create or update run sheet. (Ambulance Crew, ETC Staff)
    """
    try:
        return await claim_service.create_or_update_run_sheet(
            db, incident_id=incident_id, obj_in=run_sheet_in, user_id=current_user.id, state_id=state_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/claims", response_model=Claim)
async def submit_claim(
    *,
    db: AsyncSession = Depends(get_db),
    claim_in: ClaimCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.CLAIM_CREATE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Submit a new claim. (Ambulance Crew, ETC Staff)
    """
    # Validation of incident state
    from src.services.incident import incident_service
    incident = await incident_service.get_by_uuid_or_id(db, id=claim_in.incident_id, state_id=state_id)
    if not incident:
        raise HTTPException(status_code=400, detail="Incident not found or access denied")
        
    return await claim_service.create_claim(
        db, 
        incident_id=claim_in.incident_id, 
        user_id=current_user.id, 
        claim_type=claim_in.claim_type, 
        amount=claim_in.amount,
        distance_km=claim_in.distance_km
    )

@router.get("/", response_model=List[ClaimPair])
async def list_claims(
    *,
    db: AsyncSession = Depends(get_db),
    filters: ClaimFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.CLAIM_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    List all claims (returned in pairs per incident).
    """
    return await claim_service.get_claims_paginated(
        db, filters=filters, skip=skip, limit=limit, state_id=state_id
    )

@router.get("/export")
async def export_claims(
    *,
    db: AsyncSession = Depends(get_db),
    filters: ClaimFilter = Depends(),
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.CLAIM_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Response:
    """
    Export claims as CSV.
    """
    csv_content = await claim_service.export_claims_csv(db, filters=filters, state_id=state_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=claims_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.get("/{id}", response_model=ClaimDetail)
async def read_claim(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.CLAIM_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Get detailed claim information.
    """
    claim = await claim_service.get_claim_detail(db, claim_id=id, state_id=state_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@router.patch("/{id}/process", response_model=Claim)
async def process_claim(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    process_in: ClaimUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.CLAIM_APPROVE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Approve or Reject a claim. (Claims Staff, Admins)
    """
    try:
        claim = await claim_service.process_claim(
            db, 
            claim_id=id, 
            status=process_in.status, 
            processor_id=current_user.id, 
            state_id=state_id,
            reason=process_in.rejection_reason
        )
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
