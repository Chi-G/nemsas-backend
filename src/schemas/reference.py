from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class StateBase(BaseModel):
    name: str
    population: int = 0

class State(StateBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LGABase(BaseModel):
    state_id: int
    name: str

class LGA(LGABase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DrugBase(BaseModel):
    name: str
    dosage_form: Optional[str] = None
    is_nhia_approved: bool = True

class Drug(DrugBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
