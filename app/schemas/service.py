from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.schemas.fee_category import FeeCategory

class ServiceBase(BaseModel):
    code: Optional[str] = ""
    description: Optional[str] = None
    price: float = 0.0
    fee_category_id: Optional[int] = Field(None, alias="feeCategoryId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ServiceCreate(ServiceBase):
    id: int

class ServiceUpdate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    date_added: Optional[datetime] = Field(None, alias="dateAdded")
    fee_category: Optional[FeeCategory] = Field(None, alias="feeCategory")

