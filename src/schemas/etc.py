from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from src.db.models.claim import ClaimStatus, ClaimType

class ETCIntakeBase(BaseModel):
    incident_id: int
    arrival_time: datetime
    initial_assessment: str
    triage_category: str
    interventions: Optional[str] = None

class ETCIntakeCreate(ETCIntakeBase):
    pass

class ETCIntakeRead(ETCIntakeBase):
    id: int
    etc_facility_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ETCClaimCreate(BaseModel):
    incident_id: int
    amount: float
    notes: Optional[str] = None

class ETCClaimRead(BaseModel):
    id: int
    incident_id: int
    claim_type: ClaimType
    amount: float
    status: ClaimStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
