from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Any, Union
from uuid import UUID
from app.schemas.patient import Patient

class IncidentBase(BaseModel):
    serial_no: Optional[str] = Field(None, alias="serialNo")
    location_label: Optional[str] = Field(None, alias="incidentLocation")
    street: Optional[str] = Field(None, alias="street")
    district_ward: Optional[str] = Field(None, alias="districtWard")
    area_council: Optional[str] = Field(None, alias="areaCouncil")
    zip_code: Optional[str] = Field(None, alias="zipCode")
    latitude: Optional[float] = Field(None, alias="latitude")
    longitude: Optional[float] = Field(None, alias="longitude")
    
    caller_name: Optional[str] = Field(None, alias="callerName")
    caller_phone: Optional[str] = Field(None, alias="callerNumber")
    caller_is_patient: Optional[str] = Field(None, alias="callerIsPatient")
    
    incident_category: Optional[str] = Field(None, alias="incidentCategory")
    triage_category: Optional[str] = Field(None, alias="triageCategory")
    description: Optional[str] = Field(None, alias="description")
    recommendation: Optional[str] = Field(None, alias="recommendation")
    
    can_resolve_without_ambulance: Optional[bool] = Field(None, alias="canResolveWithoutAmbulance")
    treatment_center: Optional[str] = Field(None, alias="treatmentCenter")
    
    mass_casualty: Optional[bool] = Field(False, alias="massCasualty")
    total_patients: Optional[int] = Field(None, alias="totalPatients")
    
    incident_date: Optional[str] = Field(None, alias="incidentDate")
    incident_time: Optional[str] = Field(None, alias="incidentTime")
    
    dispatch_date: Optional[str] = Field(None, alias="dispatchDate")
    dispatch_full_name: Optional[str] = Field(None, alias="dispatchFullName")
    dispatcher_id: Optional[UUID] = Field(None, alias="dispatcherId")
    
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(IncidentBase):
    status: Optional[str] = None

class Incident(IncidentBase):
    id: int
    status: Optional[str] = None
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    
    # ViewModel Mappings
    patient_view_model: Optional[Patient] = Field(None, alias="patientViewModel")
    ambulance_view_model: Optional[Any] = Field(None, alias="ambulanceViewModel")
    etc_view_model: Optional[Any] = Field(None, alias="emergencyTreatmentCenterViewModel")
    
    @model_validator(mode='before')
    @classmethod
    def map_nested_models(cls, data: Any) -> Any:
        # If this is an ORM object, look for relationships
        if hasattr(data, 'patients') and data.patients:
            # Assuming primary patient is the first one for simplistic ViewModel delivery
            data.patient_view_model = data.patients[0]
        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class IncidentListContainer(BaseModel):
    items: List[Incident]

class IncidentPaginatedResponse(BaseModel):
    success: bool
    message: str
    data: IncidentListContainer
    totalCount: int = 0
    refreshToken: Optional[str] = None

class IncidentResponse(BaseModel):
    success: bool
    message: str
    data: Incident
