from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
from app.schemas.state import State

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

class Monitoring(MonitoringBase):
    id: int
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    added_by: Optional[str] = Field(None, alias="addedBy")
    is_active: bool = Field(True, alias="isActive")
    
    state: Optional[State] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
