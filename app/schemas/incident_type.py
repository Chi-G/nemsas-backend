from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class IncidentTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class IncidentTypeCreate(IncidentTypeBase):
    id: Optional[int] = None

class IncidentTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class IncidentType(IncidentTypeBase):
    id: int
    date_added: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=lambda s: "".join(
            word.capitalize() if i > 0 else word for i, word in enumerate(s.split("_"))
        )
    )

class IncidentTypeResponse(BaseModel):
    success: bool = True
    message: str = "Incident Type(s) successfully fetched"
    data: List[IncidentType]
    total_count: int
    refresh_token: Optional[str] = None
    refresh_token_expiry_time: str = "0001-01-01T00:00:00"

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda s: "".join(
            word.capitalize() if i > 0 else word for i, word in enumerate(s.split("_"))
        )
    )

IncidentTypeResponse.model_rebuild()
