from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict, Field

class AmbulanceTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class AmbulanceTypeCreate(AmbulanceTypeBase):
    id: Optional[int] = None
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

class AmbulanceType(AmbulanceTypeBase):
    id: int
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class AmbulanceTypeResponse(BaseModel):
    success: bool = True
    message: str = "Ambulance Type(s) successfully fetched"
    data: Union[List[AmbulanceType], AmbulanceType, None]
    totalCount: int = 0
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: str = "0001-01-01T00:00:00"
