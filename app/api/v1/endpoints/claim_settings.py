from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud.claim_setting import claim_setting
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

class ClaimSettingUpdate(BaseModel):
    value: str

@router.get("/{key}")
async def get_claim_setting(
    key: str,
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Get a claim setting by key.
    Accessible to all users (unprotected).
    """
    setting = await claim_setting.get_by_key(db, key=key)
    if not setting:
        raise HTTPException(status_code=404, detail="Claim setting not found")
    
    return {
        "success": True,
        "message": "Claim setting fetched successfully",
        "data": {
            "id": setting.id,
            "key": setting.key,
            "value": setting.value,
            "dateUpdated": setting.date_updated,
            "updatedBy": setting.updated_by_id
        }
    }

@router.patch("/{key}")
async def update_claim_setting(
    key: str,
    setting_in: ClaimSettingUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Update a claim setting value.
    Uses the authenticated user's ID as updated_by_id.
    """
    class UpdateObj:
        pass
    obj_in = UpdateObj()
    obj_in.key = key
    obj_in.value = setting_in.value

    setting = await claim_setting.create_or_update(db, obj_in=obj_in, user_id=current_user.id)
    
    return {
        "success": True,
        "message": "Claim setting updated successfully",
        "data": {
            "id": setting.id,
            "key": setting.key,
            "value": setting.value,
            "dateUpdated": setting.date_updated,
            "updatedBy": setting.updated_by_id
        }
    }
