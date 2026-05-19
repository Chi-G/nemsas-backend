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
    
    total_price: Optional[float] = Field(None, alias="totalPrice")
    distance_covered: Optional[float] = Field(None, alias="distanceCovered")
    
    incident_date: Optional[str] = Field(None, alias="incidentDate")
    status: Optional[str] = Field("New", alias="status")
    review: Optional[str] = Field(None, alias="review")
    etc_review: Optional[str] = Field(None, alias="etcReview")
    
    incident_id: Optional[int] = Field(None, alias="incidentId")
    patient_id: Optional[int] = Field(None, alias="patientId")

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
        elif hasattr(data, "__dict__") and "incident" in data.__dict__:
            if data.incident:
                data.incident_view_model = data.incident
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
