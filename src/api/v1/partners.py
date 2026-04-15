from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.base import get_db
from src.db.models.user import User
from src.db.models.partner import Partner, PledgeStatus, FacilityRequestStatus
from src.schemas.partner import (
    PartnerRegister, PartnerVerifyOTP, PartnerRead,
    PledgeCreate, PledgeRead, PledgeStatusUpdate,
    FacilityRequestCreate, FacilityRequestRead
)
from src.services.partner import partner_service
from src.api import deps
from src.core.rbac import Permission as PermissionEnum
from sqlalchemy import select

router = APIRouter()

async def get_current_partner(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Partner:
    result = await db.execute(select(Partner).where(Partner.user_id == current_user.id))
    partner = result.scalars().first()
    if not partner:
        raise HTTPException(status_code=403, detail="Not a registered partner")
    return partner

@router.post("/register", response_model=PartnerRead)
async def register_partner(
    *,
    db: AsyncSession = Depends(get_db),
    partner_in: PartnerRegister
) -> Any:
    """
    Self-register as a partner. Triggers 2FA OTP.
    """
    return await partner_service.register_partner(db, obj_in=partner_in)

@router.post("/verify-otp", response_model=PartnerRead)
async def verify_partner_otp(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: PartnerVerifyOTP
) -> Any:
    """
    Verify registration OTP.
    """
    return await partner_service.verify_partner_otp(db, obj_in=verify_in)

@router.patch("/{id}/approve", response_model=PartnerRead)
async def approve_partner(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.PARTNER_MANAGE]))
) -> Any:
    """
    Admin approval of a partner account. (NEMSAS Admin only)
    """
    return await partner_service.approve_partner(db, partner_id=id, admin_id=current_user.id)

# Pledge Endpoints
@router.post("/pledges", response_model=PledgeRead)
async def create_pledge(
    *,
    db: AsyncSession = Depends(get_db),
    pledge_in: PledgeCreate,
    current_partner: Partner = Depends(get_current_partner)
) -> Any:
    """
    Submit a new ambulance pledge. (Partner only)
    """
    return await partner_service.create_pledge(db, partner_id=current_partner.id, obj_in=pledge_in)

@router.get("/pledges", response_model=List[PledgeRead])
async def read_pledges(
    *,
    db: AsyncSession = Depends(get_db),
    status: Optional[PledgeStatus] = None,
    state_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    List pledges. Partners see their own; Admins see all.
    """
    partner_id = None
    # If not Admin, restrict to self
    # Assuming PARTNER_MANAGE permission implies Admin capability
    if not any(p.name == PermissionEnum.PARTNER_MANAGE for p in current_user.role.permissions):
        result = await db.execute(select(Partner).where(Partner.user_id == current_user.id))
        partner = result.scalars().first()
        if not partner:
            raise HTTPException(status_code=403, detail="Access denied")
        partner_id = partner.id

    return await partner_service.get_pledges(db, partner_id=partner_id, status=status, state_id=state_id)

@router.patch("/pledges/{id}/status", response_model=PledgeRead)
async def update_pledge_status(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    status_in: PledgeStatusUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.PARTNER_MANAGE]))
) -> Any:
    """
    Update pledge status. (Admin only)
    """
    return await partner_service.update_pledge_status(db, pledge_id=id, status_in=status_in.status, admin_id=current_user.id)

# Facility Request Endpoints
@router.post("/facility-requests", response_model=FacilityRequestRead)
async def create_facility_request(
    *,
    db: AsyncSession = Depends(get_db),
    request_in: FacilityRequestCreate,
    current_partner: Partner = Depends(get_current_partner)
) -> Any:
    """
    Submit a new health facility registry request. (Partner only)
    """
    return await partner_service.create_facility_request(db, partner_id=current_partner.id, obj_in=request_in)

@router.patch("/facility-requests/{id}/approve")
async def approve_facility_request(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.PARTNER_MANAGE]))
) -> Any:
    """
    Approve facility request and add to registry. (Admin only)
    """
    return await partner_service.approve_facility_request(db, request_id=id, admin_id=current_user.id)
