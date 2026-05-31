from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, List, Union, Any

class AmbulanceBase(BaseModel):
    location: Optional[str] = None
    ambulance_type_id: Optional[int] = Field(None, alias="ambulanceTypeId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    ward_id: Optional[int] = Field(None, alias="wardId")
    nhia_or_shia: Optional[str] = Field(None, alias="nhiAorSHIA")
    service_type: Optional[str] = Field(None, alias="serviceType")
    online: Optional[bool] = True
    driver_name: Optional[str] = Field(None, alias="driverName")
    contact_number: Optional[str] = Field(None, alias="contactNumber")
    state_name: Optional[str] = Field(None, alias="stateName")
    event_status_type: Optional[str] = Field(None, alias="eventStatusType")
    plate_number: Optional[str] = Field(None, alias="plateNumber")
    make: Optional[str] = Field(None, alias="make")
    year: Optional[str] = Field(None, alias="year")
    model: Optional[str] = Field(None, alias="model")
    accreditation_type: Optional[str] = Field(None, alias="accreditationType")
    vehicle_ownership_type: Optional[str] = Field(None, alias="vehicleOwnershipType")


    model_config = ConfigDict(populate_by_name=True)




class AmbulanceCreate(AmbulanceBase):
    name: str
    code: Optional[str] = None


class AmbulanceUpdate(AmbulanceBase):
    name: Optional[str] = None
    code: Optional[str] = None

class AmbulanceInDBBase(AmbulanceBase):
    id: int
    name: str
    code: str
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Ambulance(AmbulanceInDBBase):

    ambulance_type_view_model: Optional[Any] = Field(None, alias="ambulanceTypeViewModel")
    runsheet_view_model: Optional[Any] = Field(None, alias="runsheetViewModel")
    
    @model_validator(mode='before')
    @classmethod
    def sync_state_name(cls, data: Any) -> Any:
        # If the state relationship is loaded, use its name as the primary source
        if hasattr(data, 'state') and data.state:
            data.state_name = data.state.name
        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)



class AmbulanceSummary(BaseModel):
    id: int
    name: str
    code: str
    location: Optional[str] = None
    ambulance_type_id: Optional[int] = Field(None, alias="ambulanceTypeId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    ward_id: Optional[int] = Field(None, alias="wardId")
    nhia_or_shia: Optional[str] = Field(None, alias="nhiAorSHIA")
    service_type: Optional[str] = Field(None, alias="serviceType")
    online: bool = True
    driver_name: Optional[str] = Field(None, alias="driverName")
    contact_number: Optional[str] = Field(None, alias="contactNumber")
    state_name: Optional[str] = Field(None, alias="stateName")
    lga_name: Optional[str] = Field(None, alias="lgaName")
    ambulance_type_name: Optional[str] = Field(None, alias="ambulanceTypeName")
    plate_number: Optional[str] = Field(None, alias="plateNumber")
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    ambulance_type_view_model: Optional[Any] = Field(None, alias="ambulanceTypeViewModel")
    runsheet_view_model: Optional[Any] = Field(None, alias="runsheetViewModel")
    event_status_type: Optional[str] = Field(None, alias="eventStatusType")

    @model_validator(mode='before')
    @classmethod
    def sync_names(cls, data: Any) -> Any:
        if hasattr(data, 'state') and data.state:
            data.state_name = data.state.name
        if hasattr(data, 'lga') and data.lga:
            data.lga_name = data.lga.name
        if hasattr(data, 'ambulance_type') and data.ambulance_type:
            data.ambulance_type_name = data.ambulance_type.name
        return data

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AmbulanceResponse(BaseModel):
    success: bool
    message: str
    data: Union[Ambulance, List[Ambulance], List[AmbulanceSummary]]
    totalCount: int
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: str = "0001-01-01T00:00:00"

