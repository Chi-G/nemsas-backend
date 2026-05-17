from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ClaimImageBase(BaseModel):
    claim_id: Optional[int] = Field(None, alias="claimId")
    claim_title: Optional[str] = Field(None, alias="claimTitle")
    incident_id: Optional[int] = Field(None, alias="incidentId")
    image_url: Optional[str] = Field(None, alias="imageUrl")
    is_etc: Optional[bool] = Field(False, alias="isEtc")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ClaimImageCreate(ClaimImageBase):
    id: int

class ClaimImageUpdate(ClaimImageBase):
    pass

class ClaimImage(ClaimImageBase):
    id: int
