from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class EtcInterventionBase(BaseModel):
    drug_id: Optional[int] = Field(None, alias="drugId")
    medical_intervention: Optional[str] = Field(None, alias="medicalIntervention")
    price: Optional[float] = Field(None, alias="price")
    dose: Optional[float] = Field(None, alias="dose")
    diagnosis: Optional[str] = Field(None, alias="diagnosis")
    quantity: Optional[int] = Field(None, alias="quantity")
    ambulance_id: Optional[int] = Field(None, alias="ambulanceId")
    emergency_treatment_center_id: Optional[int] = Field(None, alias="emergencyTreatmentCenterId")
    incident_id: Optional[int] = Field(None, alias="incident_Id")
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class EtcInterventionCreate(EtcInterventionBase):
    id: int

class EtcInterventionUpdate(EtcInterventionBase):
    pass

class EtcIntervention(EtcInterventionBase):
    id: int
