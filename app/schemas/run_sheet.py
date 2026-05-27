from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from app.schemas.patient import Patient
from app.schemas.user import User
from app.schemas.incident import Incident
from app.schemas.ambulance import AmbulanceSummary
from app.schemas.hospital import HospitalSummary

def get_loaded_relation(obj: Any, attr_name: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(attr_name)
    try:
        from sqlalchemy import inspect
        cls = type(obj)
        if hasattr(cls, "__mapper__"):
            if attr_name in cls.__mapper__.relationships:
                inspected = inspect(obj)
                if inspected is not None:
                    if attr_name not in inspected.unloaded:
                        return getattr(obj, attr_name, None)
                return None
    except Exception:
        return None
    return getattr(obj, attr_name, None)

def orm_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, list):
        return [orm_to_dict(item) for item in obj]
    if isinstance(obj, dict): 
        return {k: orm_to_dict(v) for k, v in obj.items()}
        
    cls = type(obj)
    if hasattr(cls, "__mapper__"):
        try:
            from sqlalchemy import inspect
            inspected = inspect(obj)
            if inspected is not None:
                res = {}
                for col in inspected.mapper.column_attrs:
                    res[col.key] = getattr(obj, col.key, None)
                for rel in inspected.mapper.relationships:
                    if rel.key not in inspected.unloaded:
                        val = getattr(obj, rel.key, None)
                        res[rel.key] = orm_to_dict(val)
                for k, v in obj.__dict__.items():
                    if k not in res and not k.startswith('_'):
                        res[k] = orm_to_dict(v)
                return res
        except Exception:
            pass
            
    return obj

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
    user_id: Optional[UUID] = Field(None, alias="userId")
    hospice_user_id: Optional[UUID] = Field(None, alias="hospiceUserId")

    @model_validator(mode='before')
    @classmethod
    def map_incoming_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Map userId / medicUserId / medicuserId / user_id to medic_user_id and user_id
            for k in ["userId", "medicUserId", "medicuserId", "user_id"]:
                if k in data and data[k] is not None:
                    if not data.get("medic_user_id") and not data.get("medicUserId"):
                        data["medic_user_id"] = data[k]
                    if not data.get("user_id") and not data.get("userId"):
                        data["user_id"] = data[k]
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
        route_from_val = get_loaded_relation(data, "route_from")
        if not route_from_val:
            incident = get_loaded_relation(data, "incident")
            if incident:
                incident_loc = get_loaded_relation(incident, "incident_location")
                if incident_loc:
                    if isinstance(data, dict):
                        data["route_from"] = incident_loc
                    else:
                        setattr(data, "route_from", incident_loc)

        # Map user
        medic_user = get_loaded_relation(data, "medic_user")
        if medic_user:
            if isinstance(data, dict):
                data["user"] = medic_user
            else:
                setattr(data, "user", medic_user)

        # Populate patients and patientViewModels
        # REMOVED: Frontend complained about massive payload duplication (patients, patientViewModels, patientViewModel all had same data)
        incident = get_loaded_relation(data, "incident")
        # if incident:
        #     incident_patients = get_loaded_relation(incident, "patients")
        #     if incident_patients:
        #         if isinstance(data, dict):
        #             data["patients"] = []
        #             data["patientViewModels"] = []
        #         else:
        #             setattr(data, "patients", [])
        #             setattr(data, "patientViewModels", [])

        # Map patientViewModel from runsheet.patient relationship
        patient_obj = get_loaded_relation(data, "patient")
        if patient_obj:
            if isinstance(data, dict):
                data["patient_view_model"] = patient_obj
            else:
                setattr(data, "patient_view_model", patient_obj)
        else:
            # Fallback to the first patient from the incident if no specific runsheet.patient is assigned
            if incident:
                patients_list = get_loaded_relation(incident, "patients")
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
            etc_obj = get_loaded_relation(incident, "hospital")
            if etc_obj:
                if isinstance(data, dict):
                    data["emergency_treatment_center_view_model"] = etc_obj
                else:
                    setattr(data["emergency_treatment_center_view_model"] if isinstance(data, dict) else data, "emergency_treatment_center_view_model", etc_obj)

        # Map ambulanceViewModel from runsheet.ambulance relationship (or fallback to incident.ambulance)
        amb_obj = get_loaded_relation(data, "ambulance")
        if not amb_obj and incident:
            amb_obj = get_loaded_relation(incident, "ambulance")
            
        if amb_obj:
            if isinstance(data, dict):
                data["ambulance_view_model"] = amb_obj
            else:
                setattr(data, "ambulance_view_model", amb_obj)

        # Map price (dynamically from incident claims of type Ambulance)
        price_val = 0.0
        if incident:
            claims_list = get_loaded_relation(incident, "claims")
            if claims_list:
                for claim in claims_list:
                    claim_type_val = get_loaded_relation(claim, "claim_type")
                    claim_type_str = claim_type_val.value if hasattr(claim_type_val, "value") else str(claim_type_val)
                    if claim_type_str and claim_type_str.lower().endswith("ambulance"):
                        claim_price = get_loaded_relation(claim, "total_price")
                        if not claim_price:
                            claim_price = get_loaded_relation(claim, "amount") or 0.0
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
        medic_user = get_loaded_relation(data, "medic_user")
        if medic_user:
            medic_state = get_loaded_relation(medic_user, "state")
            if medic_state:
                state_name_val = get_loaded_relation(medic_state, "name")
        if not state_name_val and incident:
            state_name_val = get_loaded_relation(incident, "state_name")
            if not state_name_val:
                incident_state = get_loaded_relation(incident, "state")
                if incident_state:
                    state_name_val = get_loaded_relation(incident_state, "name")
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
