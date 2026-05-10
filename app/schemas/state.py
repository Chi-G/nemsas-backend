from pydantic import BaseModel
from typing import Optional

class StateBase(BaseModel):
    id: int
    name: str
    code: Optional[str] = ""

class StateCreate(StateBase):
    pass

class StateUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class State(StateBase):
    class Config:
        from_attributes = True
