from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional, Any, List

class MonitoringBase(BaseModel):
    year: int
    month: int
    no_of_transport: int = Field(0, alias="noOfTransport")
    no_of_mamii_lgas: int = Field(0, alias="noOfMamiiLGAs")
    by_tricycle_ambulance: int = Field(0, alias="byTricycleAmbulance")
    by_nurtw_driver: int = Field(0, alias="byNurtwDriver")
    bls: int = Field(0, alias="bls")
    labor_transportation: int = Field(0, alias="laborTransportation")
    obstetric_transportation: int = Field(0, alias="obstetricTransportation")
    neonatal_transportation: int = Field(0, alias="neonatalTransportation")
    bemonc: int = Field(0, alias="bemonc")
    cemonc: int = Field(0, alias="cemonc")
    maternal_mortalities: int = Field(0, alias="maternalMortalities")
    neonatal_mortalities: int = Field(0, alias="neonatalMortalities")
    remark: Optional[str] = None
    
    state_id: Optional[int] = Field(None, alias="stateId")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class MonitoringCreate(MonitoringBase):
    pass

class MonitoringUpdate(MonitoringBase):
    pass

class MonitoringState(BaseModel):
    id: int
    name: str
    code: Optional[str] = ""
    lgas: List[Any] = []
    date_added: Optional[datetime] = Field(datetime.fromisoformat("2023-07-05T07:27:52+00:00"), alias="dateAdded")
    added_by: Optional[str] = Field("", alias="addedBy")
    updated_at: Optional[datetime] = Field(datetime.fromisoformat("2023-07-05T07:27:52+00:00"), alias="updatedAt")
    updated_by: Optional[str] = Field(None, alias="updatedBy")
    is_active: bool = Field(True, alias="isActive")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def check_orm(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return {
                "id": getattr(data, "id"),
                "name": getattr(data, "name"),
                "code": getattr(data, "code", "") or "",
                "lgas": [],
                "dateAdded": datetime.fromisoformat("2023-07-05T07:27:52+00:00"),
                "addedBy": "",
                "updatedAt": datetime.fromisoformat("2023-07-05T07:27:52+00:00"),
                "updatedBy": None,
                "isActive": True
            }
        return data

class Monitoring(MonitoringBase):
    id: int
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    added_by: Optional[str] = Field(None, alias="addedBy")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    updated_by: Optional[str] = Field(None, alias="updatedBy")
    is_active: bool = Field(True, alias="isActive")
    
    state: Optional[MonitoringState] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class MonitoringListResponse(BaseModel):
    message: str = "Monthly data fetched successfully"
    data: List[Monitoring]

class MonthlyAggregateData(BaseModel):
    month: str = Field(..., alias="month")
    no_of_transport: int = Field(0, alias="noOfTransport")
    no_of_mamii_lgas: int = Field(0, alias="noOfMamiiLGAs")
    by_tricycle_ambulance: int = Field(0, alias="byTricycleAmbulance")
    by_nurtw_driver: int = Field(0, alias="byNurtwDriver")
    bls: int = Field(0, alias="bls")
    labor_transportation: int = Field(0, alias="laborTransportation")
    obstetric_transportation: int = Field(0, alias="obstetricTransportation")
    neonatal_transportation: int = Field(0, alias="neonatalTransportation")
    bemonc: int = Field(0, alias="bemonc")
    cemonc: int = Field(0, alias="cemonc")
    maternal_mortalities: int = Field(0, alias="maternalMortalities")
    neonatal_mortalities: int = Field(0, alias="neonatalMortalities")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class MonthlyAggregateResponse(BaseModel):
    message: str = "Monthly data fetched successfully"
    data: List[MonthlyAggregateData]

