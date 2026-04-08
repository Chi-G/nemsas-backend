from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from src.db.models.claim import ClaimStatus, ClaimType

class RunSheetBase(BaseModel):
    incident_id: int
    patient_data: Optional[dict] = None
    drugs_administered: Optional[list] = None

class RunSheetUpdate(BaseModel):
    patient_data: Optional[dict] = None
    drugs_administered: Optional[list] = None
    crew_signature: Optional[str] = None
    etc_signature: Optional[str] = None

class RunSheet(RunSheetBase):
    id: int
    crew_signature: Optional[str] = None
    crew_signed_at: Optional[datetime] = None
    crew_id: Optional[int] = None
    etc_signature: Optional[str] = None
    etc_signed_at: Optional[datetime] = None
    etc_staff_id: Optional[int] = None
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClaimBase(BaseModel):
    incident_id: int
    claim_type: ClaimType
    amount: float
    distance_km: Optional[float] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    rejection_reason: Optional[str] = None

class Claim(ClaimBase):
    id: int
    user_id: int
    status: ClaimStatus
    rejection_reason: Optional[str] = None
    processed_at: Optional[datetime] = None
    processed_by_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ETCIntakeBase(BaseModel):
    incident_id: int
    arrival_time: datetime
    initial_assessment: str
    triage_category: str
    interventions: Optional[str] = None

class ETCIntakeCreate(ETCIntakeBase):
    etc_facility_id: int

class ETCIntake(ETCIntakeBase):
    id: int
    etc_facility_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
