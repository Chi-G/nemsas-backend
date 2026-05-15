from pydantic import BaseModel, ConfigDict, computed_field, Field, alias_generators
from typing import Optional, List, Any
from datetime import datetime, date
from uuid import UUID
from app.schemas.patient import Patient, PatientCreate

class IncidentBase(BaseModel):
    caller_name: Optional[str] = Field(None, alias="callerName")
    caller_number: Optional[str] = Field(None, alias="callerNumber")
    incident_date: Optional[date] = Field(None, alias="incidentDate")
    incident_time: Optional[str] = Field(None, alias="incidentTime")
    description: Optional[str] = None
    recommendation: Optional[str] = None
    triage_category: Optional[str] = Field(None, alias="triageCategory")
    incident_location: Optional[str] = Field(None, alias="incidentLocation")
    district_ward: Optional[str] = Field(None, alias="districtWard")
    street: Optional[str] = None
    area_council: Optional[str] = Field(None, alias="areaCouncil")
    zip_code: Optional[str] = Field(None, alias="zipCode")
    incident_category_id: Optional[int] = Field(None, alias="incidentCategoryId")
    can_resolve_without_ambulance: Optional[bool] = Field(None, alias="canResolveWithoutAmbulance")
    treatment_center: Optional[str] = Field(None, alias="treatmentCenter")
    dispatch_full_name: Optional[str] = Field(None, alias="dispatchFullName")
    dispatcher_id: Optional[UUID] = Field(None, alias="dispatcherId")
    dispatch_date: Optional[date] = Field(None, alias="dispatchDate")
    supervisor_first_name: Optional[str] = Field(None, alias="supervisorFirstName")
    supervisor_middle_name: Optional[str] = Field(None, alias="supervisorMiddleName")
    supervisor_last_name: Optional[str] = Field(None, alias="supervisorLastName")
    supervisor_date: Optional[date] = Field(None, alias="supervisorDate")
    serial_no: Optional[str] = Field(None, alias="serialNo")
    caller_is_patient: Optional[str] = Field(None, alias="callerIsPatient")
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    mass_casualty: Optional[bool] = Field(False, alias="massCasualty")
    total_patients: Optional[int] = Field(None, alias="totalPatients")
    incident_status_type: Optional[str] = Field(None, alias="incidentStatusType")
    event_status_type: Optional[str] = Field(None, alias="eventStatusType")
    state_name: Optional[str] = Field(None, alias="stateName")
    state_id: Optional[int] = Field(None, alias="stateId")
    etc_id: Optional[int] = Field(None, alias="emergencyTreatmentCenterId")
    ambulance_id: Optional[int] = Field(None, alias="ambulanceId")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class IncidentCreate(IncidentBase):
    patients: List[PatientCreate] = []
    # For handling string-based category name in payload
    incident_category: Optional[str] = Field(None, alias="incidentCategory")
    ambulance_type: Optional[str] = Field(None, alias="ambulanceType")
    ambulance_name: Optional[str] = Field(None, alias="ambulanceName")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        alias_generator=alias_generators.to_camel
    )

class IncidentUpdate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    date_added: Optional[datetime] = None
    patients: List[Patient] = []
    
    # Internal relationship fields for computed properties
    incident_type: Optional[Any] = Field(None, exclude=True)
    state: Optional[Any] = Field(None, exclude=True)

    @computed_field(alias="incidentTypeName")
    @property
    def incident_type_name(self) -> Optional[str]:
        if self.incident_type:
            return self.incident_type.name
        return None

    @computed_field(alias="stateName")
    @property
    def state_name_computed(self) -> Optional[str]:
        if self.state:
            return self.state.name
        return None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class IncidentSummary(BaseModel):
    id: int
    serial_no: Optional[str] = None
    caller_name: Optional[str] = None
    incident_date: Optional[date] = None
    triage_category: Optional[str] = None
    incident_status_type: Optional[str] = None
    event_status_type: Optional[str] = None
    state_id: Optional[int] = None
    total_patients: Optional[int] = None
    mass_casualty: Optional[bool] = False
    incident_location: Optional[str] = None
    incident_category_id: Optional[int] = None
    date_added: Optional[datetime] = None
    patients: List[Patient] = []
    
    # Internal relationship fields for computed properties
    incident_type: Optional[Any] = Field(None, exclude=True)
    state: Optional[Any] = Field(None, exclude=True)

    @computed_field(alias="incidentTypeName")
    @property
    def incident_type_name(self) -> Optional[str]:
        if self.incident_type:
            return self.incident_type.name
        return None

    @computed_field(alias="stateName")
    @property
    def state_name_computed(self) -> Optional[str]:
        if self.state:
            return self.state.name
        return None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class IncidentResponse(BaseModel):
    success: bool
    message: str
    data: List[IncidentSummary]
    total: int
