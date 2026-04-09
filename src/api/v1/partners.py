from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.partner import Partner, PartnerCreate, Pledge, PledgeBase, PledgeCreate, FacilityRequest, FacilityRequestBase, FacilityRequestCreate
from src.services.partner import partner_service
from src.db.models.user import User
from src.core.rbac import Permission as PermissionEnum

router = APIRouter()

@router.post("/register", response_model=Partner)
async def register_partner(
    *,
    db: AsyncSession = Depends(get_db),
    partner_in: PartnerCreate,
    current_active_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.PARTNER_MANAGE])),
) -> Any:
    """
    Register an organisation as a partner. (Admins only)
    """
    return await partner_service.create_partner(db, obj_in=partner_in)

@router.post("/pledges", response_model=Pledge)
async def create_pledge(
    *,
    db: AsyncSession = Depends(get_db),
    pledge_in: PledgeBase,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.FLEET_MANAGE])),
) -> Any:
    """
    Create a new ambulance pledge. (Partners only)
    """
    partner = await partner_service.get_partner_by_user_id(db, user_id=current_user.id)
    if not partner:
        raise HTTPException(status_code=403, detail="Not a registered partner")
        
    pledge_create = PledgeCreate(**pledge_in.dict(), partner_id=partner.id)
    return await partner_service.create_pledge(db, obj_in=pledge_create)

@router.post("/facility-requests", response_model=FacilityRequest)
async def create_facility_request(
    *,
    db: AsyncSession = Depends(get_db),
    request_in: FacilityRequestBase,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.FLEET_MANAGE])),
) -> Any:
    """
    Submit a request for a new health facility. (Partners only)
    """
    partner = await partner_service.get_partner_by_user_id(db, user_id=current_user.id)
    if not partner:
        raise HTTPException(status_code=403, detail="Not a registered partner")
        
    request_create = FacilityRequestCreate(**request_in.dict(), partner_id=partner.id)
    return await partner_service.create_facility_request(db, obj_in=request_create)

@router.post("/facility-requests/{id}/approve", response_model=Any)
async def approve_facility_request(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.PARTNER_MANAGE])),
) -> Any:
    """
    Approve a facility request and add to the registry. (Admins only)
    """
    return await partner_service.approve_facility_request(db, request_id=id)
