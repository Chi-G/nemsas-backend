from fastapi import APIRouter, Depends
from app.api import deps
from app.partners.models import PartnerUser
from app.partners.schemas import PartnerUserResponse
from app.schemas.common import ResponseBase

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
