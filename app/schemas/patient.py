from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from datetime import datetime, date
from typing import Optional, List, Any, Dict

class PatientBase(BaseModel):
    first_name: Optional[str] = Field(None, alias="firstName")
    middle_name: Optional[str] = Field(None, alias="middleName")
    last_name: Optional[str] = Field(None, alias="lastName")
    do_b: Optional[date] = Field(None, alias="doB")
    sex: Optional[int] = Field(None, alias="sex")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    nhia: Optional[str] = Field(None, alias="nhia")
    address: Optional[str] = Field(None, alias="address")
    
    incident_id: Optional[int] = Field(None, alias="incident_id")
    ambulance_id: Optional[int] = Field(None, alias="ambulance_Id")
    etc_id: Optional[int] = Field(None, alias="etC_id")
    
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    @field_validator('do_b', mode='before')
    @classmethod
    def parse_dob(cls, value):
        if isinstance(value, str):
            try:
                from datetime import datetime
                return datetime.strptime(value, "%d/%m/%Y").date()
            except ValueError:
                pass
        return value

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    
    # Relationship with real MedicalIntervention model or EtcIntervention
    interventions: Optional[List[Any]] = Field(default=[], alias="interventions")
    
    # Populated dynamically from incident's etc_interventions
    medical_interventions: Optional[List[Dict[str, Any]]] = Field(default=None, alias="medicalInterventions")
    drugs: Optional[List[Dict[str, Any]]] = Field(default=None, alias="drugs")

    etc_medical_interventions: Optional[List[Dict[str, Any]]] = Field(default=None, alias="etcMedicalInterventions")
    etc_drugs: Optional[List[Dict[str, Any]]] = Field(default=None, alias="etcDrugs")

    notes: Optional[List[Any]] = Field(default=None, alias="notes")
    runsheet: Optional[Any] = Field(None, alias="runsheet")
    extra_details: Optional[Any] = Field(None, alias="extraDetails")

    # Internal field to receive injected etc_interventions from parent Incident schema
    # Excluded from serialization output
    _etc_interventions: List[Any] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode='before')
    @classmethod
    def serialize_relations(cls, data: Any) -> Any:
        if isinstance(data, dict):
            invs = data.get('interventions')
            if isinstance(invs, list):
                new_invs = []
                for item in invs:
                    if not isinstance(item, dict) and hasattr(item, "__dict__"):
                        from app.schemas.medical_intervention import MedicalIntervention as MedSchema
                        new_invs.append(MedSchema.model_validate(item).model_dump(by_alias=True))
                    else:
                        new_invs.append(item)
                data['interventions'] = new_invs
        elif hasattr(data, "__dict__"):
            res = {}
            if hasattr(data, "__table__"):
                for col in data.__table__.columns:
                    res[col.name] = getattr(data, col.name)
            
            for key in ["id", "created_at", "first_name", "middle_name", "last_name", "do_b", "sex", "phone_number", "nhia", "address", "incident_id", "ambulance_id", "etc_id", "medical_interventions", "notes", "drugs", "runsheet", "extra_details"]:
                if hasattr(data, key) and not isinstance(getattr(data, key), (list, tuple)):
                    res[key] = getattr(data, key)
                    
            # Safe check to prevent lazy loading of 'interventions' relationship
            invs = []
            if 'interventions' in data.__dict__:
                invs = data.interventions or []
                
            new_invs = []
            for item in invs:
                if not isinstance(item, dict) and hasattr(item, "__dict__"):
                    from app.schemas.medical_intervention import MedicalIntervention as MedSchema
                    new_invs.append(MedSchema.model_validate(item).model_dump(by_alias=True))
                else:
                    new_invs.append(item)
            res['interventions'] = new_invs
            
            # Carry over dynamic properties
            for prop in ['medical_interventions', 'drugs', 'etc_medical_interventions', 'etc_drugs', 'etcMedicalInterventions', 'etcDrugs']:
                if hasattr(data, prop):
                    res[prop] = getattr(data, prop)
            return res
        return data

    def populate_interventions_from_etc(self, etc_interventions: List[Any]) -> None:
        """
        Split the incident's etc_interventions into medical_interventions and drugs
        based on the suffix of the `medical_intervention` field:
          - Ends with '- Procedure'  → medical_interventions
          - Ends with '- Drug'       → drugs
        """
        procedures = []
        drug_list = []

        for item in etc_interventions:
            # Check patient ID
            if isinstance(item, dict):
                item_patient_id = item.get("patient_id")
            else:
                item_patient_id = getattr(item, "patient_id", None)
                
            if item_patient_id is not None and item_patient_id != self.id:
                continue
                
            # Support both ORM objects and dicts
            if isinstance(item, dict):
                name = item.get("medical_intervention") or ""
                row: Dict[str, Any] = {
                    "id": item.get("id"),
                    "drugId": item.get("drug_id"),
                    "medicalIntervention": name,
                    "price": item.get("price"),
                    "dose": item.get("dose"),
                    "diagnosis": item.get("diagnosis"),
                    "quantity": item.get("quantity"),
                    "dateAdded": item.get("date_added"),
                }
            else:
                name = getattr(item, "medical_intervention", "") or ""
                row = {
                    "id": getattr(item, "id", None),
                    "drugId": getattr(item, "drug_id", None),
                    "medicalIntervention": name,
                    "price": getattr(item, "price", None),
                    "dose": getattr(item, "dose", None),
                    "diagnosis": getattr(item, "diagnosis", None),
                    "quantity": getattr(item, "quantity", None),
                    "dateAdded": getattr(item, "date_added", None),
                }

            lower = name.lower()
            if lower.endswith("- drug"):
                drug_list.append(row)
            elif lower.endswith("- procedure"):
                procedures.append(row)
            else:
                # Fallback: non-categorised items go to procedures
                procedures.append(row)

        self.etc_medical_interventions = procedures if procedures else []
        self.etc_drugs = drug_list if drug_list else []

class PatientResponse(BaseModel):
    success: bool
    message: str
    data: Patient

from app.schemas.medical_intervention import MedicalIntervention
Patient.model_rebuild()

