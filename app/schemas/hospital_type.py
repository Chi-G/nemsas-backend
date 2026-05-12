from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict, Field

class HospitalTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class HospitalTypeCreate(HospitalTypeBase):
    id: Optional[int] = None
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

class HospitalType(HospitalTypeBase):
    id: int
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class HospitalTypeResponse(BaseModel):
    success: bool = True
    message: str = "Hospital Type(s) successfully fetched"
    data: Union[List[HospitalType], HospitalType, None] # Use the HospitalType schema here
    totalCount: int = 0
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: str = "0001-01-01T00:00:00"
