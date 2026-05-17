from pydantic import BaseModel, ConfigDict, computed_field, Field, alias_generators
from typing import Optional, List, Any
from datetime import datetime, date
from uuid import UUID
from app.schemas.patient import Patient, PatientCreate
from app.schemas.hospital import Hospital as HospitalSchema
from app.schemas.claim_image import ClaimImage

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
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")
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

class IncidentClaim(BaseModel):
    id: int
    title: Optional[str] = Field(None, alias="title")
    patient_name: Optional[str] = Field(None, alias="patientName")
    ambulance_type: Optional[str] = Field(None, alias="ambulanceType")
    incident_category: Optional[str] = Field(None, alias="incidentCategory")
    nhia: Optional[str] = Field(None, alias="nhia")
    location: Optional[str] = Field(None, alias="location")
    service_provider: Optional[str] = Field(None, alias="serviceProvider")
    total_price: Optional[float] = Field(None, alias="totalPrice")
    distance_covered: Optional[float] = Field(None, alias="distanceCovered")
    incident_date: Optional[str] = Field(None, alias="incidentDate")
    status: Optional[str] = Field("New", alias="status")
    review: Optional[str] = Field(None, alias="review")
    etc_review: Optional[str] = Field(None, alias="etcReview")
    incident_id: Optional[int] = Field(None, alias="incidentId")
    patient_id: Optional[int] = Field(None, alias="patientId")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    images: Optional[List[ClaimImage]] = Field(default_factory=list, alias="images")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class IncidentUpdate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    date_added: Optional[datetime] = None
    patients: List[Patient] = []
    hospital: Optional[HospitalSchema] = Field(None, alias="emergencyTreatmentCenter")
    
    incident_type_name: Optional[str] = Field(None, alias="incidentTypeName")
    state_name_computed: Optional[str] = Field(None, alias="stateName")
    claims: List[IncidentClaim] = Field(default_factory=list, alias="claims")

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
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    date_added: Optional[datetime] = None
    patients: List[Patient] = []
    hospital: Optional[HospitalSchema] = Field(None, alias="emergencyTreatmentCenter")
    
    incident_type_name: Optional[str] = Field(None, alias="incidentTypeName")
    state_name_computed: Optional[str] = Field(None, alias="stateName")
    claims: List[IncidentClaim] = Field(default_factory=list, alias="claims")

    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True,
        alias_generator=alias_generators.to_camel
    )

class IncidentResponse(BaseModel):
    success: bool
    message: str
    data: List[IncidentSummary]
    total: int

class SingleIncidentResponse(BaseModel):
    success: bool
    message: str
    data: Incident
