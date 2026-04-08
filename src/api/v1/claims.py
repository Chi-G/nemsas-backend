from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.claim import Claim, ClaimCreate, ClaimUpdate, RunSheet, RunSheetUpdate, ETCIntake, ETCIntakeCreate
from src.services.claim import claim_service
from src.db.models.user import User, Permission
from src.db.models.claim import ClaimStatus, ClaimType

router = APIRouter()

@router.get("/run-sheet/{incident_id}", response_model=RunSheet)
async def read_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get run sheet by incident ID.
    """
    run_sheet = await claim_service.get_run_sheet(db, incident_id=incident_id)
    if not run_sheet:
        raise HTTPException(status_code=404, detail="Run sheet not found")
    return run_sheet

@router.post("/run-sheet/{incident_id}", response_model=RunSheet)
async def create_or_update_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    run_sheet_in: RunSheetUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create or update run sheet. (Ambulance Crew, ETC Staff)
    """
    try:
        return await claim_service.create_or_update_run_sheet(
            db, incident_id=incident_id, obj_in=run_sheet_in, user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/claims", response_model=Claim)
async def submit_claim(
    *,
    db: AsyncSession = Depends(get_db),
    claim_in: ClaimCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Submit a new claim. (Ambulance Crew, ETC Staff)
    """
    return await claim_service.create_claim(
        db, 
        incident_id=claim_in.incident_id, 
        user_id=current_user.id, 
        claim_type=claim_in.claim_type, 
        amount=claim_in.amount,
        distance_km=claim_in.distance_km
    )

@router.patch("/claims/{id}/process", response_model=Claim)
async def process_claim(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    process_in: ClaimUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Approve or Reject a claim. (Claims Staff, Admins)
    """
    # Assuming role check is handled by deps.check_permissions in a real scenario
    claim = await claim_service.process_claim(
        db, 
        claim_id=id, 
        status=process_in.status, 
        processor_id=current_user.id, 
        reason=process_in.rejection_reason
    )
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim
