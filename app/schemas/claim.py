from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Any, Dict
from app.schemas.patient import Patient
from app.schemas.incident import Incident

class ClaimBase(BaseModel):
    title: Optional[str] = Field(None, alias="title")
    patient_name: Optional[str] = Field(None, alias="patientName")
    ambulance_type: Optional[str] = Field(None, alias="ambulanceType")
    incident_category: Optional[str] = Field(None, alias="incidentCategory")
    nhia: Optional[str] = Field(None, alias="nhia")
    location: Optional[str] = Field(None, alias="location")
    service_provider: Optional[str] = Field(None, alias="serviceProvider")
    claim_type: Optional[str] = Field(None, alias="claimType")
    
    total_price: Optional[float] = Field(None, alias="totalPrice")
    distance_covered: Optional[float] = Field(None, alias="distanceCovered")
    
    incident_date: Optional[str] = Field(None, alias="incidentDate")
    ambulance_claim_status: Optional[str] = Field("New", alias="ambulanceClaimStatus")
    etc_claim_status: Optional[str] = Field("New", alias="etcClaimStatus")
    review: Optional[str] = Field(None, alias="review")
    etc_review: Optional[str] = Field(None, alias="etcReview")
    
    incident_id: Optional[int] = Field(None, alias="incidentId")
    patient_id: Optional[int] = Field(None, alias="patientId")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ClaimCreate(ClaimBase):
    image_url: Optional[str] = Field(None, alias="imageUrl")

class ClaimUpdate(ClaimBase):
    pass

from app.schemas.claim_image import ClaimImage

class Claim(ClaimBase):
    id: int
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    status: Optional[str] = None
    
    patient: Optional[Patient] = None
    incident_view_model: Optional[Incident] = Field(None, alias="incidentViewModel")
    images: Optional[List[ClaimImage]] = Field(default_factory=list, alias="images")
    
    # Response Compatibility fields
    details: List[Any] = Field(default_factory=list, alias="details")
    medical_interventions: List[Any] = Field(default_factory=list, alias="medicalInterventions")
    drugs_list: Optional[List[Any]] = Field(default_factory=list, alias="drugsList")
    patient_details: Optional[Dict[str, Any]] = Field(None, alias="patientDetails")

    @model_validator(mode='before')
    @classmethod
    def map_nested(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'incident' in data:
                data['incident_view_model'] = data['incident']
            
            claim_type = data.get('claim_type') or data.get('claimType')
            patient = data.get('patient')
            
            details = []
            med_interventions = []
            drugs_list = []
            
            if patient:
                interventions = patient.get('interventions') if isinstance(patient, dict) else getattr(patient, 'interventions', None)
                if not interventions:
                    interventions = patient.get('medical_interventions') if isinstance(patient, dict) else getattr(patient, 'medical_interventions', None)
                if not isinstance(interventions, list):
                    interventions = []
                else:
                    interventions = [
                        {k: v for k, v in item.__dict__.items() if not k.startswith('_')} if hasattr(item, '__dict__') else item
                        for item in interventions
                    ]
                
                drugs = patient.get('drugs') if isinstance(patient, dict) else getattr(patient, 'drugs', None)
                if isinstance(drugs, list):
                    drugs_list = [
                        {k: v for k, v in item.__dict__.items() if not k.startswith('_')} if hasattr(item, '__dict__') else item
                        for item in drugs
                    ]
                elif isinstance(drugs, dict):
                    drugs_list = [drugs]
                elif isinstance(drugs, str) and drugs:
                    import json
                    try:
                        parsed = json.loads(drugs)
                        if isinstance(parsed, list):
                            drugs_list = parsed
                        else:
                            drugs_list = [parsed]
                    except Exception:
                        drugs_list = [drugs]
                elif drugs:
                    drugs_list = [drugs]
                else:
                    drugs_list = []
                
                claim_type_val = claim_type.value if hasattr(claim_type, "value") else str(claim_type)
                claim_type_str = str(claim_type_val).upper() if claim_type_val else ""
                if claim_type_str.endswith("ETC"):
                    # We will map details to ETC Interventions later.
                    med_interventions = interventions
                else:
                    details = drugs_list
                    med_interventions = []
            
            # We construct patient_details representation here
            patient_details = None
            if patient:
                patient_details = {}
                if isinstance(patient, dict):
                    patient_details.update(patient)
                elif hasattr(patient, "__dict__"):
                    for k, v in patient.__dict__.items():
                        if not k.startswith("_"):
                            patient_details[k] = v
                patient_details["interventions"] = details # Will be overridden if ETC
                patient_details["medicalInterventions"] = med_interventions
                patient_details["drugs"] = drugs_list
            
            claim_type_val = claim_type.value if hasattr(claim_type, "value") else str(claim_type)
            claim_type_str = str(claim_type_val).upper() if claim_type_val else ""
            if claim_type_str.endswith("ETC"):
                data['status'] = data.get('etc_claim_status') or data.get('etcClaimStatus')
                
                incident_data = data.get('incident')
                
                if incident_data and isinstance(incident_data, dict):
                    etc_interventions = incident_data.get('etc_interventions') or []
                    total_price = 0.0
                    drugs_from_etc = []
                    meds_from_etc = []
                    
                    patient_id = data.get("patient_id") or data.get("patientId")
                    if patient_id is None and patient and isinstance(patient, dict):
                        patient_id = patient.get("id")
                    
                    for item in etc_interventions:
                        item_patient_id = item.get("patient_id") if isinstance(item, dict) else getattr(item, "patient_id", None)
                        if item_patient_id is not None and patient_id is not None and item_patient_id != patient_id:
                            continue
                            
                        name = item.get("medical_intervention", "") or ""
                        
                        row = {
                            "id": item.get("id"),
                            "drugId": item.get("drug_id"),
                            "medicalIntervention": name,
                            "price": item.get("price"),
                            "dose": item.get("dose"),
                            "diagnosis": item.get("diagnosis"),
                            "quantity": item.get("quantity"),
                            "dateAdded": item.get("date_added"),
                        }
                        
                        if name.lower().endswith("- drug"):
                            drugs_from_etc.append(row)
                        else:
                            meds_from_etc.append(row)
                            
                        price = item.get("price") or 0.0
                        quantity = item.get("quantity") or 0.0
                        total_price += float(price) * float(quantity)
                            
                    data['total_price'] = total_price
                    data['totalPrice'] = total_price
                        
                    details = meds_from_etc
                    if not med_interventions:
                        med_interventions = meds_from_etc
                    
                    if not drugs_list:
                        drugs_list = drugs_from_etc
                        
                    if patient_details:
                        patient_details["interventions"] = meds_from_etc
                        patient_details["drugs"] = drugs_list
                        
                elif incident_data and hasattr(incident_data, "etc_interventions"):
                    etc_interventions = incident_data.etc_interventions or []
                    total_price = 0.0
                    drugs_from_etc = []
                    meds_from_etc = []
                    
                    patient_id = getattr(data, "patient_id", None)
                    if patient_id is None and patient and hasattr(patient, "id"):
                        patient_id = patient.id
                        
                    for item in etc_interventions:
                        item_patient_id = getattr(item, "patient_id", None)
                        if item_patient_id is not None and patient_id is not None and item_patient_id != patient_id:
                            continue
                            
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
                        
                        if name.lower().endswith("- drug"):
                            drugs_from_etc.append(row)
                        else:
                            meds_from_etc.append(row)
                            
                        price = getattr(item, "price", 0.0) or 0.0
                        quantity = getattr(item, "quantity", 0.0) or 0.0
                        total_price += float(price) * float(quantity)
                            
                    data['total_price'] = total_price
                    data['totalPrice'] = total_price
                        
                    if not med_interventions:
                        med_interventions = meds_from_etc
                        details = meds_from_etc
                    if not drugs_list:
                        drugs_list = drugs_from_etc
            else:
                data['status'] = data.get('ambulance_claim_status') or data.get('ambulanceClaimStatus')
                
            data['details'] = details
            data['medical_interventions'] = med_interventions
            data['drugs_list'] = drugs_list
            data['patient_details'] = patient_details
            
        elif hasattr(data, "__dict__"):
            if "incident" in data.__dict__ and data.incident:
                data.incident_view_model = data.incident
            
            claim_type = getattr(data, 'claim_type', None)
            patient = getattr(data, 'patient', None)
            
            details = []
            med_interventions = []
            drugs_list = []
            
            if patient:
                interventions = getattr(patient, 'interventions', None)
                if not interventions:
                    interventions = getattr(patient, 'medical_interventions', None)
                if not isinstance(interventions, list):
                    interventions = []
                else:
                    interventions = [
                        {k: v for k, v in item.__dict__.items() if not k.startswith('_')} if hasattr(item, '__dict__') else item
                        for item in interventions
                    ]
                
                drugs = getattr(patient, 'drugs', None)
                if isinstance(drugs, list):
                    drugs_list = [
                        {k: v for k, v in item.__dict__.items() if not k.startswith('_')} if hasattr(item, '__dict__') else item
                        for item in drugs
                    ]
                elif isinstance(drugs, dict):
                    drugs_list = [drugs]
                elif isinstance(drugs, str) and drugs:
                    import json
                    try:
                        parsed = json.loads(drugs)
                        if isinstance(parsed, list):
                            drugs_list = parsed
                        else:
                            drugs_list = [parsed]
                    except Exception:
                        drugs_list = [drugs]
                elif drugs:
                    drugs_list = [drugs]
                else:
                    drugs_list = []
                
                claim_type_val = claim_type.value if hasattr(claim_type, "value") else str(claim_type)
                claim_type_str = str(claim_type_val).upper() if claim_type_val else ""
                if claim_type_str.endswith("ETC"):
                    med_interventions = interventions
                else:
                    details = drugs_list
                    med_interventions = []
            
            patient_details = None
            if patient:
                patient_details = {}
                if hasattr(patient, "__dict__"):
                    for k, v in patient.__dict__.items():
                        if not k.startswith("_"):
                            patient_details[k] = v
                patient_details["interventions"] = details
                patient_details["medicalInterventions"] = med_interventions
                patient_details["drugs"] = drugs_list
            
            claim_type_val = claim_type.value if hasattr(claim_type, "value") else str(claim_type)
            claim_type_str = str(claim_type_val).upper() if claim_type_val else ""
            if claim_type_str.endswith("ETC"):
                data.status = getattr(data, 'etc_claim_status', None)
                
                if getattr(data, 'incident', None) and getattr(data.incident, 'etc_interventions', None):
                    total_price = 0.0
                    drugs_from_etc = []
                    meds_from_etc = []
                    
                    c_patient_id = getattr(data, "patient_id", None)
                    if c_patient_id is None and patient and hasattr(patient, "id"):
                        c_patient_id = patient.id
                    
                    for item in data.incident.etc_interventions:
                        item_patient_id = getattr(item, "patient_id", None)
                        if item_patient_id is not None and c_patient_id is not None and item_patient_id != c_patient_id:
                            continue
                            
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
                        
                        if name.lower().endswith("- drug"):
                            drugs_from_etc.append(row)
                        else:
                            meds_from_etc.append(row)
                            
                        price = getattr(item, "price", 0.0) or 0.0
                        quantity = getattr(item, "quantity", 0.0) or 0.0
                        total_price += float(price) * float(quantity)
                    
                    data.total_price = total_price
                        
                    details = meds_from_etc
                    if not med_interventions:
                        med_interventions = meds_from_etc
                    
                    if not drugs_list:
                        drugs_list = drugs_from_etc
                        
                    if patient_details:
                        patient_details["interventions"] = meds_from_etc
                        patient_details["drugs"] = drugs_list
            else:
                data.status = getattr(data, 'ambulance_claim_status', None)
                
            data.details = details
            data.medical_interventions = med_interventions
            data.drugs_list = drugs_list
            data.patient_details = patient_details
            
        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ClaimListContainer(BaseModel):
    items: List[Claim]

class ClaimPaginatedResponse(BaseModel):
    success: bool
    message: str
    data: ClaimListContainer
    totalCount: int = 0

class ClaimResponse(BaseModel):
    success: bool
    message: str
    data: Claim

class ClaimSummaryData(BaseModel):
    total: int = 0
    approved: int = 0
    rejected: int = 0
    pending: int = 0

class ClaimSummaryResponse(BaseModel):
    success: bool = True
    message: str = "Claim summary retrieved successfully"
    data: Any
    totalCount: int = 1
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: Optional[str] = "0001-01-01T00:00:00"
