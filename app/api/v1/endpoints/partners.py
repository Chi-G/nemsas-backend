from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.partners.models import PartnerUser
from app.partners.schemas import PartnerUserResponse, PartnerChangePassword
from app.schemas.common import ResponseBase
from app.core.security import verify_password, get_password_hash

router = APIRouter()

@router.get("/me", response_model=ResponseBase[PartnerUserResponse])
async def read_partner_me(
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
):
    """
    Get current partner user details using partner token
    """
    return {
        "success": True,
        "message": "Partner details successfully fetched",
        "data": current_partner
    }

@router.post("/change-password", response_model=ResponseBase)
async def change_partner_password(
    data: PartnerChangePassword,
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
):
    """
    Change partner password
    """
    if not verify_password(data.current_password, current_partner.hashed_password):
        raise HTTPException(status_code=400, detail={"message": "Incorrect current password", "error": "INVALID_PASSWORD"})
    
    current_partner.hashed_password = get_password_hash(data.new_password)
    db.add(current_partner)
    await db.commit()
    
    return {
        "success": True,
        "message": "Password changed successfully",
        "data": None
    }

from typing import List
from sqlalchemy.future import select

@router.get("/all", response_model=ResponseBase[List[PartnerUserResponse]])
async def read_all_partners(
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
):
    """
    Get all partner users (partners and organizations). Only accessible by admins.
    """
    if current_partner.user_type not in ["SUPERADMINISTRATOR", "ADMINSEMSASUSER", "admin"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")

    result = await db.execute(select(PartnerUser))
    partners = result.scalars().all()
    
    return {
        "success": True,
        "message": "All partners fetched successfully",
        "data": partners
    }
