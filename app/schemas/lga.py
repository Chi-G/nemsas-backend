from pydantic import BaseModel, Field
from typing import Optional, Any

class LGABase(BaseModel):
    id: int
    name: str
    code: Optional[str] = ""
    state_id: int = Field(..., alias="stateId")
    state_view_model: Optional[Any] = Field(None, alias="stateViewModel")

    class Config:
        populate_by_name = True
        from_attributes = True

class LGACreate(LGABase):
    pass

class LGAUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    state_id: Optional[int] = None

class LGA(LGABase):
    pass
