from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class StateBase(BaseModel):
    name: str
    population: int = 0

class State(StateBase):
    id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LGABase(BaseModel):
    state_id: int
    name: str

class LGA(LGABase):
    id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StateWithLGAs(State):
    lgas: List[LGA]

class DrugBase(BaseModel):
    name: str
    dosage_form: Optional[str] = None
    is_nhia_approved: bool = True

class DrugCreate(DrugBase):
    pass

class DrugUpdate(BaseModel):
    name: Optional[str] = None
    dosage_form: Optional[str] = None
    is_nhia_approved: Optional[bool] = None
    is_active: Optional[bool] = None

class Drug(DrugBase):
    id: int
    is_active: bool
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AmbulanceTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class AmbulanceTypeCreate(AmbulanceTypeBase):
    pass

class AmbulanceType(AmbulanceTypeBase):
    id: int
    is_active: bool
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AccreditationCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class AccreditationCategoryCreate(AccreditationCategoryBase):
    pass

class AccreditationCategory(AccreditationCategoryBase):
    id: int
    is_active: bool
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SystemAuditLogRead(BaseModel):
    id: int
    table_name: str
    record_id: int
    action: str
    changes: Optional[dict] = None
    user_id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
