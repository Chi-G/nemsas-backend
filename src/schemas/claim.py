from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from src.db.models.claim import ClaimStatus, ClaimType

from src.schemas.run_sheet import RunSheet, RunSheetUpdate

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

class ClaimFilter(BaseModel):
    claim_type: Optional[ClaimType] = None
    status: Optional[ClaimStatus] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ClaimDetail(Claim):
    incident_uuid: str
    ambulance_plate: Optional[str] = None
    ambulance_type: Optional[str] = None
    run_sheet_status: Optional[str] = None
    is_fully_signed: bool = False
    patient_name: Optional[str] = None
    drug_list: List[str] = []
    calculation_logic: str = "" # Metadata about how fee was derived

class ClaimPair(BaseModel):
    incident_id: int
    incident_uuid: str
    ambulance_claim: Optional[Claim] = None
    etc_claim: Optional[Claim] = None

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
