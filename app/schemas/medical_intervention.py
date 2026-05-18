from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, Any

class MedicalInterventionBase(BaseModel):
    patient_id: int
    is_alert: bool = False
    can_speak: bool = False
    is_in_pain: bool = False
    un_responsive: bool = False
    
    main_complaint: Optional[str] = None
    primary_survey: Optional[str] = None
    physical_examination_findings: Optional[str] = None
    
    iv_fluid_type: Optional[str] = None
    size_of_fluid: Optional[str] = None
    location_of_iv_infusion: Optional[str] = None
    total_iv_fluid_volume_given: Optional[str] = None
    
    oxygen: Optional[str] = None
    remarks: Optional[str] = None
    
    pulse: Optional[int] = None
    blood_pressure: Optional[str] = None
    resp: Optional[int] = None
    glucose: Optional[int] = None
    sp02: Optional[int] = None
    
    notes: Optional[str] = None
    medical_intervention_details: Optional[str] = Field(None, alias="mediicalIntervention")
    incident_drugs: Optional[List[Any]] = Field(default=[], alias="incidentDrugs")
    
    date_added: Optional[datetime] = None
    time_taken: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=lambda s: "".join(
            word.capitalize() if i > 0 else word for i, word in enumerate(s.split("_"))
        )
    )

class MedicalInterventionCreate(MedicalInterventionBase):
    pass

class MedicalInterventionUpdate(MedicalInterventionBase):
    patient_id: Optional[int] = None

class MedicalInterventionInDBBase(MedicalInterventionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class MedicalIntervention(MedicalInterventionInDBBase):
    pass

class MedicalInterventionInDB(MedicalInterventionInDBBase):
    pass
