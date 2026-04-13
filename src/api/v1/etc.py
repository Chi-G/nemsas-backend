from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api import deps
from src.db.base import get_db
from src.core.rbac import Permission, RoleName
from src.schemas.etc import ETCIntakeCreate, ETCIntakeRead, ETCClaimCreate, ETCClaimRead
from src.schemas.incident import Incident as IncidentSchema
from src.services.etc import ETCService
from src.db.models.user import User

router = APIRouter(tags=["ETC Operations"])

@router.get("/patients/incoming", response_model=List[IncidentSchema])
async def get_incoming_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    _: bool = Depends(deps.PermissionChecker([Permission.ETC_READ]))
):
    """
    Criterion 114: Get all active incidents assigned to the current ETC facility.
    """
    # Assuming the current user's provider_id is their facility ID
    if not current_user.provider_id:
        raise HTTPException(status_code=400, detail="User is not associated with any facility")
        
    return await ETCService.get_incoming_patients(db, current_user.provider_id)

@router.post("/intake", response_model=ETCIntakeRead)
async def create_intake(
    intake_in: ETCIntakeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    _: bool = Depends(deps.PermissionChecker([Permission.ETC_INTAKE]))
):
    """
    Criterion 110: Record patient arrival and initial assessment.
    """
    if not current_user.provider_id:
        raise HTTPException(status_code=400, detail="User is not associated with any facility")
        
    return await ETCService.create_intake(db, intake_in, current_user.provider_id)

@router.post("/run-sheets/{run_sheet_id}/cosign")
async def cosign_run_sheet(
    run_sheet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    _: bool = Depends(deps.PermissionChecker([Permission.ETC_SIGN]))
):
    """
    Criterion 116: ETC staff co-signs a clinical run sheet.
    """
    return await ETCService.cosign_run_sheet(db, run_sheet_id, current_user.id)

@router.post("/claims", response_model=ETCClaimRead)
async def create_claim(
    claim_in: ETCClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    _: bool = Depends(deps.PermissionChecker([Permission.CLAIM_CREATE]))
):
    """
    Criterion 119: Healthcare facility submits their own claim.
    """
    return await ETCService.create_hospital_claim(db, claim_in, current_user.id)
