from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.device import Device, DeviceCreate
from app.crud.device import device_crud
from app.models.user import User
from app.schemas.common import ResponseBase

router = APIRouter()

@router.post("/register", response_model=ResponseBase[Device])
async def register_device(
    *,
    db: AsyncSession = Depends(deps.get_db),
    device_in: DeviceCreate,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Register a new device for push notifications
    """
    device = await device_crud.create(db, obj_in=device_in, user_id=current_user.id)
    return {
        "success": True,
        "message": "Device successfully registered",
        "data": device
    }

@router.get("/me", response_model=ResponseBase[List[Device]])
async def get_my_devices(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all registered devices for the current user
    """
    devices = await device_crud.get_multi_by_user(db, user_id=current_user.id)
    return {
        "success": True,
        "message": "Devices fetched",
        "data": devices
    }

@router.delete("/{device_id}", response_model=ResponseBase[bool])
async def unregister_device(
    *,
    db: AsyncSession = Depends(deps.get_db),
    device_id: str,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Unregister/Delete a device
    """
    # Verify ownership
    device = await device_crud.get(db, id=device_id)
    if not device or device.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await device_crud.remove(db, id=device_id)
    return {
        "success": True,
        "message": "Device successfully unregistered",
        "data": True
    }
