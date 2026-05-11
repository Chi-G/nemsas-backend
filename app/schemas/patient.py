from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional, List, Any

class PatientBase(BaseModel):
    first_name: Optional[str] = Field(None, alias="firstName")
    middle_name: Optional[str] = Field(None, alias="middleName")
    last_name: Optional[str] = Field(None, alias="lastName")
    do_b: Optional[datetime] = Field(None, alias="doB")
    sex: Optional[str] = Field(None, alias="sex")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    nhia: Optional[str] = Field(None, alias="nhia")
    address: Optional[str] = Field(None, alias="address")
    
    incident_id: Optional[int] = Field(None, alias="incident_Id")
    ambulance_id: Optional[int] = Field(None, alias="ambulance_Id")
    etc_id: Optional[int] = Field(None, alias="etC_Id")
    
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    
    # Placeholder lists consistent with ViewModel outputs
    medical_interventions: Optional[List[Any]] = Field(default=None, alias="medicalInterventions")
    notes: Optional[List[Any]] = Field(default=None, alias="notes")
    drugs: Optional[Any] = Field(None, alias="drugs")
    runsheet: Optional[Any] = Field(None, alias="runsheet")
    extra_details: Optional[Any] = Field(None, alias="extraDetails")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class PatientResponse(BaseModel):
    success: bool
    message: str
    data: Patient
