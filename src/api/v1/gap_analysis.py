from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.deps import get_db, get_current_user, PermissionChecker
from src.schemas.gap_analysis import NationalSummaryResponse, RegionSummaryResponse, PartnerContributionResponse
from src.services.gap_analysis import GapAnalysisService
from src.db.models.user import User
from typing import List

router = APIRouter()

@router.get("/national", response_model=NationalSummaryResponse)
def get_national_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AC 191: Returns national summary metrics.
    """
    return GapAnalysisService.get_national_summary(db)

@router.get("/states", response_model=List[RegionSummaryResponse])
def get_state_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AC 192 & 198: Returns summary metrics for all 37 states.
    """
    return GapAnalysisService.get_state_summaries(db)

@router.get("/states/{state_id}/lgas", response_model=List[RegionSummaryResponse])
def get_lga_summaries(
    state_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AC 193: Returns summary metrics for all LGAs within a state.
    """
    return GapAnalysisService.get_lga_summaries(db, state_id)

@router.get("/my-contributions", response_model=List[PartnerContributionResponse])
def get_my_contributions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AC 195: Returns ambulances attributed to the authenticated partner.
    """
    return GapAnalysisService.get_partner_contributions(db, current_user.id)

@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def trigger_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    check_perm = Depends(PermissionChecker(["ADMIN"]))
):
    """
    Manual trigger for the nightly gap analysis sync (AC 197).
    Restricted to Admins.
    """
    GapAnalysisService.sync_gap_analysis_data(db)
    return {"message": "Gap analysis data synchronized successfully"}
