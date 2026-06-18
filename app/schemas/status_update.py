from pydantic import BaseModel
from typing import Literal

class AmbulanceStatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "out of service", "under maintenance"]

class HospitalStatusUpdate(BaseModel):
    status: Literal["approved", "rejected"]
