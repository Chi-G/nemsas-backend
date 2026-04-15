from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.db.models.incident import ComplianceRating, IncidentStatus, EmergencyType

class QAFilter(BaseModel):
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    ambulance_id: Optional[int] = None
    compliance_rating: Optional[ComplianceRating] = None

class QAIncidentSummary(BaseModel):
    id: int
    uuid: str
    location_label: str
    emergency_type: EmergencyType
    status: IncidentStatus
    created_at: datetime
    
    # QA Specific fields
    response_time_minutes: Optional[float] = None
    ambulance_plate: Optional[str] = None
    latest_compliance_status: Optional[ComplianceRating] = None
    has_findings: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class QAFindingBase(BaseModel):
    compliance_rating: ComplianceRating
    findings_text: str

class QAFindingCreate(QAFindingBase):
    incident_id: int

class QAFindingRead(QAFindingBase):
    id: int
    incident_id: int
    created_at: datetime
    qa_officer_id: int
    qa_officer_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
