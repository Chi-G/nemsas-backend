from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.partner import Partner as PartnerSchema
from app.models.partner import Partner
from app.schemas.common import ResponseBase

router = APIRouter()

@router.get("/me", response_model=ResponseBase[PartnerSchema])
async def read_partner_me(
    current_partner: Partner = Depends(deps.get_current_partner),
):
    """
    Get current partner details using partner's token
    """
    return {
        "success": True,
        "message": "Partner details successfully fetched",
        "data": current_partner
    }
