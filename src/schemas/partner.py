from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from src.db.models.partner import PledgeStatus, FacilityRequestStatus

class PartnerBase(BaseModel):
    organisation_name: str
    contact_person: str
    contact_phone: str
    address: str

class PartnerCreate(PartnerBase):
    user_id: int

class PartnerUpdate(BaseModel):
    organisation_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None

class Partner(PartnerBase):
    id: int
    user_id: int
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PledgeBase(BaseModel):
    ambulance_count: int
    target_state_id: Optional[int] = None
    target_lga_id: Optional[int] = None

class PledgeCreate(PledgeBase):
    partner_id: int

class Pledge(PledgeBase):
    id: int
    partner_id: int
    status: PledgeStatus
    fulfilled_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FacilityRequestBase(BaseModel):
    facility_name: str
    facility_type: str
    address: str
    latitude: float
    longitude: float
    state_id: int
    lga_id: int

class FacilityRequestCreate(FacilityRequestBase):
    partner_id: int

class FacilityRequest(FacilityRequestBase):
    id: int
    partner_id: int
    status: FacilityRequestStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
