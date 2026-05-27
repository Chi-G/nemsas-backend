from datetime import datetime
from typing import Optional, List, Union, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.hospital_type import HospitalType
from app.schemas.state import State
from app.schemas.lga import LGA

class HospitalBase(BaseModel):
    name: str
    location: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    landmark: Optional[str] = None
    nhia_or_shia: Optional[str] = Field(None, alias="nhiAorSHIA")
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class HospitalCreate(HospitalBase):
    id: Optional[int] = None
    hospital_type_id: Optional[int] = Field(None, alias="hospitalTypeId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

class Hospital(HospitalBase):
    id: int
    hospital_type_id: Optional[int] = Field(None, alias="hospitalTypeId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    
    # Hydrated relationships
    hospital_type: Optional[HospitalType] = Field(None, alias="hospitalType")
    state: Optional[State] = None
    lga: Optional[LGA] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

from pydantic import model_validator

class HospitalSummary(HospitalBase):
    id: int
    hospital_type_id: Optional[int] = Field(None, alias="hospitalTypeId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    state_name: Optional[str] = Field(None, alias="stateName")
    lga_name: Optional[str] = Field(None, alias="lgaName")
    hospital_type_name: Optional[str] = Field(None, alias="hospitalTypeName")

    @model_validator(mode='before')
    @classmethod
    def sync_names(cls, data: Any) -> Any:
        if hasattr(data, 'state') and data.state:
            data.state_name = data.state.name
        if hasattr(data, 'lga') and data.lga:
            data.lga_name = data.lga.name
        if hasattr(data, 'hospital_type') and data.hospital_type:
            data.hospital_type_name = data.hospital_type.name
        return data

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    landmark: Optional[str] = None
    nhia_or_shia: Optional[str] = Field(None, alias="nhiAorSHIA")
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    hospital_type_id: Optional[int] = Field(None, alias="hospitalTypeId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class HospitalResponse(BaseModel):
    success: bool = True
    message: str = "Hospital(s) successfully fetched"
    data: Union[Hospital, List[HospitalSummary], List[Hospital], HospitalUpdate, None]
    totalCount: int = 0
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: str = "0001-01-01T00:00:00"

