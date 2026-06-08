from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.user import User

class PartnerBase(BaseModel):
    user_id: Optional[UUID] = Field(None, alias="userId")
    organisation_name: Optional[str] = Field(None, alias="organisationName")
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    contact_phone: Optional[str] = Field(None, alias="contactPhone")
    address: Optional[str] = None
    is_verified: bool = Field(False, alias="isVerified")
    user_type: Optional[str] = Field(None, alias="userType")
    token: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class PartnerCreate(PartnerBase):
    pass

class PartnerUpdate(BaseModel):
    organisation_name: Optional[str] = Field(None, alias="organisationName")
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    contact_phone: Optional[str] = Field(None, alias="contactPhone")
    address: Optional[str] = None
    is_verified: Optional[bool] = Field(None, alias="isVerified")
    user_type: Optional[str] = Field(None, alias="userType")
    token: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class Partner(PartnerBase):
    id: int
    created_at: datetime = Field(..., alias="createdAt")
    user: Optional[User] = None
