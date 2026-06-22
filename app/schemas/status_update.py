from pydantic import BaseModel
from typing import Literal

class AmbulanceStatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "pending"]

class AmbulanceActiveStatusUpdate(BaseModel):
    active_status: Literal["active", "pending", "out of service", "under maintenance"]

class HospitalStatusUpdate(BaseModel):
    status: Literal["approved", "rejected"]
