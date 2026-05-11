from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class ClaimSettingBase(BaseModel):
    key: str
    value: str

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ClaimSettingCreate(ClaimSettingBase):
    pass

class ClaimSetting(ClaimSettingBase):
    id: int
    date_updated: Optional[datetime] = Field(None, alias="dateUpdated")
    updated_by: Optional[str] = Field(None, alias="updatedBy")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
