from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.db.models.incident import IncidentStatus, EmergencyType, IncidentChannel

class IncidentStatusHistoryBase(BaseModel):
    status: IncidentStatus
    notes: Optional[str] = None

class IncidentStatusHistory(IncidentStatusHistoryBase):
    id: int
    incident_id: int
    changed_at: datetime
    changed_by_id: int
    
    model_config = ConfigDict(from_attributes=True)

class IncidentBase(BaseModel):
    location_label: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    emergency_type: EmergencyType
    severity: Optional[str] = None
    patient_count: int = 1
    notes: Optional[str] = None
    channel: IncidentChannel = IncidentChannel.APP
    location_confirmed: bool = True

class IncidentCreate(IncidentBase):
    caller_name: Optional[str] = None
    caller_phone: Optional[str] = None

class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[str] = None
    notes: Optional[str] = None

class Incident(IncidentBase):
    id: int
    uuid: str
    status: IncidentStatus
    caller_name: Optional[str] = None
    caller_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    status_history: List[IncidentStatusHistory] = []
    
    model_config = ConfigDict(from_attributes=True)

class QAFindingBase(BaseModel):
    compliance_rating: str
    findings_text: str

class QAFindingCreate(QAFindingBase):
    incident_id: int

class QAFinding(QAFindingBase):
    id: int
    incident_id: int
    created_at: datetime
    qa_officer_id: int
    
    model_config = ConfigDict(from_attributes=True)
