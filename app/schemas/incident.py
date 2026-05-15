from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional, List, Any
from datetime import datetime, date
from uuid import UUID
from app.schemas.patient import Patient

class IncidentBase(BaseModel):
    caller_name: Optional[str] = None
    caller_number: Optional[str] = None
    incident_date: Optional[date] = None
    incident_time: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    triage_category: Optional[str] = None
    incident_location: Optional[str] = None
    district_ward: Optional[str] = None
    street: Optional[str] = None
    area_council: Optional[str] = None
    zip_code: Optional[str] = None
    incident_category_id: Optional[int] = None
    can_resolve_without_ambulance: Optional[bool] = None
    treatment_center: Optional[str] = None
    dispatch_full_name: Optional[str] = None
    dispatcher_id: Optional[UUID] = None
    dispatch_date: Optional[date] = None
    supervisor_first_name: Optional[str] = None
    supervisor_middle_name: Optional[str] = None
    supervisor_last_name: Optional[str] = None
    supervisor_date: Optional[date] = None
    serial_no: Optional[str] = None
    caller_is_patient: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    mass_casualty: Optional[bool] = False
    total_patients: Optional[int] = None
    incident_status_type: Optional[str] = None
    event_status_type: Optional[str] = None
    state_name: Optional[str] = None
    state_id: Optional[int] = None
    etc_id: Optional[int] = None
    ambulance_id: Optional[int] = None

class IncidentCreate(IncidentBase):
    id: Optional[int] = None

class IncidentUpdate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    date_added: Optional[datetime] = None
    patients: List[Patient] = []

    @computed_field
    @property
    def incident_type_name(self) -> Optional[str]:
        if hasattr(self, "incident_type") and self.incident_type:
            return self.incident_type.name
        return None

    model_config = ConfigDict(from_attributes=True)

class IncidentSummary(BaseModel):
    id: int
    serial_no: Optional[str] = None
    caller_name: Optional[str] = None
    incident_date: Optional[date] = None
    triage_category: Optional[str] = None
    incident_status_type: Optional[str] = None
    event_status_type: Optional[str] = None
    state_name: Optional[str] = None
    state_id: Optional[int] = None
    total_patients: Optional[int] = None
    mass_casualty: Optional[bool] = False
    incident_location: Optional[str] = None
    incident_category_id: Optional[int] = None
    date_added: Optional[datetime] = None
    patients: List[Patient] = []
    
    @computed_field
    @property
    def incident_type_name(self) -> Optional[str]:
        # Note: This requires the relationship to be loaded in the CRUD/Endpoint
        if hasattr(self, "incident_type") and self.incident_type:
            return self.incident_type.name
        return None

    model_config = ConfigDict(from_attributes=True)

class IncidentResponse(BaseModel):
    success: bool
    message: str
    data: List[IncidentSummary]
    total: int
