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
            data['status'] = data.get('ambulance_claim_status') or data.get('ambulanceClaimStatus')
            
            # Resolve etc_interventions
            patient_data = data.get('patient')
            etc_invs = []
            if isinstance(patient_data, dict):
                etc_invs = patient_data.get('etc_interventions') or []
            elif patient_data and hasattr(patient_data, 'etc_interventions'):
                etc_invs = patient_data.etc_interventions or []
                
            if not etc_invs and 'incident' in data:
                inc_data = data['incident']
                if isinstance(inc_data, dict):
                    etc_invs = inc_data.get('etc_interventions') or []
                elif inc_data and hasattr(inc_data, 'etc_interventions'):
                    etc_invs = inc_data.etc_interventions or []

            procedures = []
            drugs = []
            serialized_etc = []
            for item in etc_invs:
                name = item.get("medical_intervention", "") if isinstance(item, dict) else getattr(item, "medical_intervention", "") or ""
                row = {
                    "id": item.get("id") if isinstance(item, dict) else getattr(item, "id", None),
                    "drugId": item.get("drug_id") if isinstance(item, dict) else getattr(item, "drug_id", None),
                    "medicalIntervention": name,
                    "price": item.get("price") if isinstance(item, dict) else getattr(item, "price", None),
                    "dose": item.get("dose") if isinstance(item, dict) else getattr(item, "dose", None),
                    "diagnosis": item.get("diagnosis") if isinstance(item, dict) else getattr(item, "diagnosis", None),
                    "quantity": item.get("quantity") if isinstance(item, dict) else getattr(item, "quantity", None),
                    "dateAdded": item.get("date_added").isoformat() if isinstance(item, dict) and item.get("date_added") and hasattr(item.get("date_added"), "isoformat") else (getattr(item, "date_added", None).isoformat() if getattr(item, "date_added", None) and hasattr(getattr(item, "date_added", None), "isoformat") else None)
                }
                serialized_etc.append(row)
                if name.lower().endswith("- drug"):
                    drugs.append(row)
                else:
                    procedures.append(row)
            
            data['details'] = serialized_etc
            data['medical_interventions'] = procedures
            data['drugs_list'] = drugs
            
            if isinstance(patient_data, dict):
                patient_data['interventions'] = serialized_etc
                patient_data['etc_medical_interventions'] = procedures
                patient_data['etc_drugs'] = drugs
                patient_data['etcMedicalInterventions'] = procedures
                patient_data['etcDrugs'] = drugs

        elif hasattr(data, "__dict__"):
            # Construct a dictionary of all properties on data to avoid directly mutating ORM relationships
            res = {}
            if hasattr(data, "__table__"):
                for col in data.__table__.columns:
                    res[col.name] = getattr(data, col.name)
            
            for key in ["id", "created_at", "title", "patient_name", "ambulance_type", "incident_category", "nhia", "location", "service_provider", "total_price", "distance_covered", "incident_date", "ambulance_claim_status", "etc_claim_status", "review", "etc_review", "incident_id", "patient_id", "rejection_reason"]:
                if hasattr(data, key) and not isinstance(getattr(data, key), (list, tuple)):
                    res[key] = getattr(data, key)
            
            res["images"] = data.images if 'images' in data.__dict__ else []
            res["incident_view_model"] = data.incident if 'incident' in data.__dict__ else None
            res["incident"] = data.incident if 'incident' in data.__dict__ else None
            res["status"] = getattr(data, "ambulance_claim_status", None)
            
            patient_obj = data.patient if 'patient' in data.__dict__ else None
            etc_invs = []
            if patient_obj and hasattr(patient_obj, "__dict__"):
                if 'etc_interventions' in patient_obj.__dict__:
                    etc_invs = patient_obj.etc_interventions or []
            if not etc_invs and 'incident' in data.__dict__ and data.incident and hasattr(data.incident, "__dict__"):
                if 'etc_interventions' in data.incident.__dict__:
                    etc_invs = data.incident.etc_interventions or []
                
            procedures = []
            drugs = []
            serialized_etc = []
            for item in etc_invs:
                name = item.get("medical_intervention", "") if isinstance(item, dict) else getattr(item, "medical_intervention", "") or ""
                row = {
                    "id": item.get("id") if isinstance(item, dict) else getattr(item, "id", None),
                    "drugId": item.get("drug_id") if isinstance(item, dict) else getattr(item, "drug_id", None),
                    "medicalIntervention": name,
                    "price": item.get("price") if isinstance(item, dict) else getattr(item, "price", None),
                    "dose": item.get("dose") if isinstance(item, dict) else getattr(item, "dose", None),
                    "diagnosis": item.get("diagnosis") if isinstance(item, dict) else getattr(item, "diagnosis", None),
                    "quantity": item.get("quantity") if isinstance(item, dict) else getattr(item, "quantity", None),
                    "dateAdded": item.get("date_added").isoformat() if isinstance(item, dict) and item.get("date_added") and hasattr(item.get("date_added"), "isoformat") else (getattr(item, "date_added", None).isoformat() if getattr(item, "date_added", None) and hasattr(getattr(item, "date_added", None), "isoformat") else None)
                }
                serialized_etc.append(row)
                if name.lower().endswith("- drug"):
                    drugs.append(row)
                else:
                    procedures.append(row)
                    
            res["details"] = serialized_etc
            res["medical_interventions"] = procedures
            res["drugs_list"] = drugs
            
            if patient_obj:
                p_dict = {}
                if hasattr(patient_obj, "__table__"):
                    for c in patient_obj.__table__.columns:
                        p_dict[c.name] = getattr(patient_obj, c.name)
                elif hasattr(patient_obj, "__dict__"):
                    p_dict = dict(patient_obj.__dict__)
                else:
                    p_dict = dict(patient_obj)
                
                # Safe to set properties on plain python dict
                p_dict["interventions"] = serialized_etc
                p_dict["etc_medical_interventions"] = procedures
                p_dict["etc_drugs"] = drugs
                p_dict["etcMedicalInterventions"] = procedures
                p_dict["etcDrugs"] = drugs
                p_dict["createdAt"] = getattr(patient_obj, "created_at", None).isoformat() if getattr(patient_obj, "created_at", None) and hasattr(getattr(patient_obj, "created_at", None), "isoformat") else None
                res["patient"] = p_dict
            else:
                res["patient"] = None
                
            return res
            
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
