from pydantic import BaseModel
from typing import List, Optional

class Organisation(BaseModel):
    name: str
    organisationType: str
    location: Optional[str] = None

class OrganisationResponse(BaseModel):
    success: bool
    message: str
    data: List[Organisation]
    totalCount: int
    refreshToken: Optional[str] = None
