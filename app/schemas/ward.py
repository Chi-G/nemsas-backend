from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class WardBase(BaseModel):
    id: int
    name: str
    code: Optional[str] = ""
    lga_id: int = Field(..., alias="lgaId")
    lga_view_model: Optional[Any] = Field(None, alias="lgaViewModel")

    class Config:
        populate_by_name = True
        from_attributes = True

class WardCreate(WardBase):
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

class WardUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    lga_id: Optional[int] = Field(None, alias="lgaId")

class Ward(WardBase):
    date_added: datetime = Field(..., alias="dateAdded")
