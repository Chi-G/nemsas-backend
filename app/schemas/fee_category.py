from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class FeeCategoryBase(BaseModel):
    code: Optional[str] = ""
    description: Optional[str] = None
    is_medicine: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class FeeCategoryCreate(FeeCategoryBase):
    id: int

class FeeCategoryUpdate(FeeCategoryBase):
    pass

class FeeCategory(FeeCategoryBase):
    id: int
    date_added: Optional[datetime] = Field(None, alias="dateAdded")

