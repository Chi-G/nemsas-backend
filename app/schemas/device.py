from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class DeviceBase(BaseModel):
    push_token: str = Field(..., alias="pushToken")
    platform: str
    device_name: Optional[str] = Field(None, alias="deviceName")
    device_id: Optional[str] = Field(None, alias="deviceId")
    ambulance_id: Optional[int] = Field(None, alias="ambulanceId")

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(DeviceBase):
    push_token: Optional[str] = Field(None, alias="pushToken")
    platform: Optional[str] = None

class Device(DeviceBase):
    id: UUID
    user_id: UUID
    last_active: datetime
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True
