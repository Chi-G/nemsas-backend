from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from app.schemas.patient import Patient
from app.schemas.user import User

class RunSheetBase(BaseModel):
    title: Optional[str] = Field(None, alias="title")
    route_from: Optional[str] = Field(None, alias="routeFrom")
    route_to: Optional[str] = Field(None, alias="routeTo")
    take_off_time: Optional[datetime] = Field(None, alias="takeOffTime")
    arrival_time: Optional[datetime] = Field(None, alias="arrivalTime")
    total_minutes_to_hospital: Optional[float] = Field(None, alias="totalMinutesToHospital")
    
    incident_id: Optional[int] = Field(None, alias="incidentId")
    patient_id: Optional[List[int]] = Field(default_factory=list, alias="patientId")
    ambulance_id: Optional[int] = Field(None, alias="ambulanceId")
    medic_user_id: Optional[UUID] = Field(None, alias="medicUserId")
    hospice_user_id: Optional[UUID] = Field(None, alias="hospiceUserId")
    emergency_treatment_center_id: Optional[int] = Field(None, alias="emergencyTreatmentCenterId")
    price: Optional[float] = Field(None, alias="price")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class RunSheetCreate(RunSheetBase):
    pass

class RunSheetUpdate(RunSheetBase):
    pass

class RunSheet(RunSheetBase):
    id: int
    status: str = "Draft"
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    
    # Related User Entities expected by frontend
    user: Optional[User] = Field(None, alias="user") # Maps to medic
    
    @model_validator(mode='before')
    @classmethod
    def map_user_and_routes(cls, data: Any) -> Any:
        if hasattr(data, 'medic_user') and data.medic_user:
            data.user = data.medic_user
            
        # Dynamically map routeFrom to incident location
        if hasattr(data, 'incident') and data.incident and not data.route_from:
            data.route_from = data.incident.incident_location
            
        # Dynamically map routeTo to ETC hospital location
        if hasattr(data, 'emergency_treatment_center') and data.emergency_treatment_center and not data.route_to:
            data.route_to = data.emergency_treatment_center.location
            
        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class RunSheetListContainer(BaseModel):
    items: List[RunSheet]

class RunSheetPaginatedResponse(BaseModel):
    success: bool
    message: str
    data: RunSheetListContainer
    totalCount: int = 0

class SingleRunSheetResponse(BaseModel):
    success: bool
    message: str
    data: RunSheet

class RunSheetAmbulance(RunSheetBase):
    id: int
    status: str = "Draft"
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    
    @model_validator(mode='before')
    @classmethod
    def map_routes(cls, data: Any) -> Any:
        if hasattr(data, 'incident') and data.incident and not data.route_from:
            data.route_from = data.incident.incident_location
            
        if hasattr(data, 'emergency_treatment_center') and data.emergency_treatment_center and not data.route_to:
            data.route_to = data.emergency_treatment_center.location
            
        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class RunSheetAmbulanceListContainer(BaseModel):
    items: List[RunSheetAmbulance]

class RunSheetAmbulancePaginatedResponse(BaseModel):
    success: bool
    message: str
    data: RunSheetAmbulanceListContainer
    totalCount: int = 0

class SingleRunSheetAmbulanceResponse(BaseModel):
    success: bool
    message: str
    data: RunSheetAmbulance
