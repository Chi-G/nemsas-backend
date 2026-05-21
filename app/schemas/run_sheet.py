from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from app.schemas.patient import Patient
from app.schemas.user import User
from app.schemas.incident import Incident
from app.schemas.ambulance import AmbulanceSummary
from app.schemas.hospital import HospitalSummary

class RunSheetBase(BaseModel):
    title: Optional[str] = Field(None, alias="title")
    route_from: Optional[str] = Field(None, alias="routeFrom")
    route_to: Optional[str] = Field(None, alias="routeTo")
    take_off_time: Optional[datetime] = Field(None, alias="takeOffTime")
    arrival_time: Optional[datetime] = Field(None, alias="arrivalTime")
    total_minutes_to_hospital: Optional[float] = Field(None, alias="totalMinutesToHospital")
    
    incident_id: Optional[int] = Field(None, alias="incidentId")
    patient_id: Optional[int] = Field(None, alias="patientId")
    ambulance_id: Optional[int] = Field(None, alias="ambulanceId")
    medic_user_id: Optional[UUID] = Field(None, alias="medicUserId")
    hospice_user_id: Optional[UUID] = Field(None, alias="hospiceUserId")

    @model_validator(mode='before')
    @classmethod
    def map_incoming_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Map userId / medicuserId / user_id to medic_user_id
            for k in ["userId", "medicuserId", "user_id"]:
                if k in data and data[k] is not None:
                    if not data.get("medic_user_id") and not data.get("medicUserId"):
                        data["medic_user_id"] = data[k]
                    break
        return data

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class RunSheetCreate(RunSheetBase):
    emergency_treatment_center_id: Optional[int] = Field(None, alias="emergencyTreatmentCenterId")
    price: Optional[float] = None

class RunSheetUpdate(RunSheetBase):
    pass

class RunSheet(RunSheetBase):
    id: int
    status: str = "Draft"
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    
    # Related User Entities expected by frontend
    user: Optional[User] = Field(None, alias="user") # Maps to medic
    
    patients: Optional[List[Patient]] = Field(None, alias="patients")
    patientViewModels: Optional[List[Patient]] = Field(None, alias="patientViewModels")
    
    # View Models matching runsheet.json exactly
    incident_view_model: Optional[Incident] = Field(None, alias="incidentViewModel")
    patient_view_model: Optional[Patient] = Field(None, alias="patientViewModel")
    ambulance_view_model: Optional[AmbulanceSummary] = Field(None, alias="ambulanceViewModel")
    emergency_treatment_center_view_model: Optional[HospitalSummary] = Field(None, alias="emergencyTreatmentCenterViewModel")
    price: Optional[float] = None
    state_name: Optional[str] = Field(None, alias="stateName")
    
    @model_validator(mode='before')
    @classmethod
    def map_fields_and_defaults(cls, data: Any) -> Any:
        # Route From Defaulting logic
        route_from_val = getattr(data, "route_from", None) or (isinstance(data, dict) and data.get("route_from"))
        if not route_from_val:
            incident = getattr(data, "incident", None) or (isinstance(data, dict) and data.get("incident"))
            if incident:
                incident_loc = getattr(incident, "incident_location", None) or (isinstance(incident, dict) and incident.get("incident_location"))
                if incident_loc:
                    if isinstance(data, dict):
                        data["route_from"] = incident_loc
                    else:
                        setattr(data, "route_from", incident_loc)

        # Map user
        medic_user = getattr(data, "medic_user", None) or (isinstance(data, dict) and data.get("medic_user"))
        if medic_user:
            if isinstance(data, dict):
                data["user"] = medic_user
            else:
                setattr(data, "user", medic_user)

        # Populate patients and patientViewModels
        incident = getattr(data, "incident", None) or (isinstance(data, dict) and data.get("incident"))
        if incident:
            incident_patients = getattr(incident, "patients", None) or (isinstance(incident, dict) and incident.get("patients"))
            if incident_patients:
                if isinstance(data, dict):
                    data["patients"] = incident_patients
                    data["patientViewModels"] = incident_patients
                else:
                    setattr(data, "patients", incident_patients)
                    setattr(data, "patientViewModels", incident_patients)

        # Map patientViewModel from runsheet.patient relationship
        patient_obj = getattr(data, "patient", None) or (isinstance(data, dict) and data.get("patient"))
        if patient_obj:
            if isinstance(data, dict):
                data["patient_view_model"] = patient_obj
            else:
                setattr(data, "patient_view_model", patient_obj)
        else:
            # Fallback to the first patient from the incident if no specific runsheet.patient is assigned
            if incident:
                patients_list = getattr(incident, "patients", None) or (isinstance(incident, dict) and incident.get("patients"))
                if patients_list and len(patients_list) > 0:
                    if isinstance(data, dict):
                        data["patient_view_model"] = patients_list[0]
                    else:
                        setattr(data, "patient_view_model", patients_list[0])

        # Map incidentViewModel
        if incident:
            if isinstance(data, dict):
                data["incident_view_model"] = incident
            else:
                setattr(data, "incident_view_model", incident)
                
            # Map emergencyTreatmentCenterViewModel from incident.hospital
            etc_obj = getattr(incident, "hospital", None) or (isinstance(incident, dict) and incident.get("hospital"))
            if etc_obj:
                if isinstance(data, dict):
                    data["emergency_treatment_center_view_model"] = etc_obj
                else:
                    setattr(data, "emergency_treatment_center_view_model", etc_obj)

        # Map ambulanceViewModel from runsheet.ambulance relationship (or fallback to incident.ambulance)
        amb_obj = getattr(data, "ambulance", None) or (isinstance(data, dict) and data.get("ambulance"))
        if not amb_obj and incident:
            amb_obj = getattr(incident, "ambulance", None) or (isinstance(incident, dict) and incident.get("ambulance"))
            
        if amb_obj:
            if isinstance(data, dict):
                data["ambulance_view_model"] = amb_obj
            else:
                setattr(data, "ambulance_view_model", amb_obj)

        # Map price (dynamically from incident claims of type Ambulance)
        price_val = 0.0
        if incident:
            claims_list = getattr(incident, "claims", None) or (isinstance(incident, dict) and incident.get("claims"))
            if claims_list:
                for claim in claims_list:
                    claim_type_val = getattr(claim, "claim_type", None) or (isinstance(claim, dict) and claim.get("claim_type"))
                    if claim_type_val and str(claim_type_val).lower() == "ambulance":
                        claim_price = getattr(claim, "total_price", 0.0) or (isinstance(claim, dict) and claim.get("total_price", 0.0))
                        price_val = float(claim_price)
                        break
        # Fallback default price for valid ambulance claims
        if price_val == 0.0:
            price_val = 35000.0
            
        if isinstance(data, dict):
            data["price"] = price_val
        else:
            setattr(data, "price", price_val)

        # Map stateName
        state_name_val = None
        medic_user = getattr(data, "medic_user", None) or (isinstance(data, dict) and data.get("medic_user"))
        if medic_user and getattr(medic_user, "state", None):
            state_name_val = medic_user.state.name
        if not state_name_val and incident:
            state_name_val = getattr(incident, "state_name", None) or (isinstance(incident, dict) and incident.get("state_name"))
            if not state_name_val and getattr(incident, "state", None):
                state_name_val = incident.state.name
        if not state_name_val:
            state_name_val = "Borno"
            
        if isinstance(data, dict):
            data["state_name"] = state_name_val
        else:
            setattr(data, "state_name", state_name_val)

        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class RunSheetListContainer(BaseModel):
    items: List[RunSheet]

class RunSheetPaginatedResponse(BaseModel):
    success: bool
    message: str
    data: RunSheetListContainer
    totalCount: int = 0

class RunSheetSingleResponse(BaseModel):
    success: bool
    message: str
    data: RunSheet
