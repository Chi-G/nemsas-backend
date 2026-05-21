from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Any
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
    status: Optional[str] = Field("New", alias="status")
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
    
    patient: Optional[Patient] = None
    incident_view_model: Optional[Incident] = Field(None, alias="incidentViewModel")
    images: Optional[List[ClaimImage]] = Field(default_factory=list, alias="images")
    
    # Response Compatibility fields
    details: List[Any] = Field(default_factory=list, alias="details")
    medical_interventions: List[Any] = Field(default_factory=list, alias="medicalInterventions")

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
            
            if patient:
                interventions = patient.get('interventions') if isinstance(patient, dict) else getattr(patient, 'interventions', None)
                if not interventions:
                    interventions = patient.get('medical_interventions') if isinstance(patient, dict) else getattr(patient, 'medical_interventions', None)
                if not isinstance(interventions, list):
                    interventions = []
                
                drugs = patient.get('drugs') if isinstance(patient, dict) else getattr(patient, 'drugs', None)
                if isinstance(drugs, list):
                    drugs_list = drugs
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
                
                claim_type_str = str(claim_type).upper() if claim_type else ""
                if claim_type_str == "ETC":
                    details = interventions
                    med_interventions = interventions
                else:
                    details = drugs_list
                    med_interventions = []
            
            data['details'] = details
            data['medical_interventions'] = med_interventions
            
        elif hasattr(data, "__dict__"):
            if "incident" in data.__dict__ and data.incident:
                data.incident_view_model = data.incident
            
            claim_type = getattr(data, 'claim_type', None)
            patient = getattr(data, 'patient', None)
            
            details = []
            med_interventions = []
            
            if patient:
                interventions = getattr(patient, 'interventions', None)
                if not interventions:
                    interventions = getattr(patient, 'medical_interventions', None)
                if not isinstance(interventions, list):
                    interventions = []
                
                drugs = getattr(patient, 'drugs', None)
                if isinstance(drugs, list):
                    drugs_list = drugs
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
                
                claim_type_str = str(claim_type).upper() if claim_type else ""
                if claim_type_str == "ETC":
                    details = interventions
                    med_interventions = interventions
                else:
                    details = drugs_list
                    med_interventions = []
            
            data.details = details
            data.medical_interventions = med_interventions
            
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
    data: ClaimSummaryData
    totalCount: int = 1
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: Optional[str] = "0001-01-01T00:00:00"
