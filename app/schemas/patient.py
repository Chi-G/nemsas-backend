from pydantic import BaseModel, ConfigDict, Field, model_validator
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

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    
    # Relationship with real MedicalIntervention model
    interventions: Optional[List["MedicalIntervention"]] = Field(default=[], alias="interventions")
    
    # Populated dynamically from incident's etc_interventions
    medical_interventions: Optional[List[Dict[str, Any]]] = Field(default=None, alias="medicalInterventions")
    drugs: Optional[List[Dict[str, Any]]] = Field(default=None, alias="drugs")

    notes: Optional[List[Any]] = Field(default=None, alias="notes")
    runsheet: Optional[Any] = Field(None, alias="runsheet")
    extra_details: Optional[Any] = Field(None, alias="extraDetails")

    # Internal field to receive injected etc_interventions from parent Incident schema
    # Excluded from serialization output
    _etc_interventions: List[Any] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

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

        self.medical_interventions = procedures if procedures else []
        self.drugs = drug_list if drug_list else []

class PatientResponse(BaseModel):
    success: bool
    message: str
    data: Patient

from app.schemas.medical_intervention import MedicalIntervention
Patient.model_rebuild()

