from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NationalSummaryResponse(BaseModel):
    national_target: int
    total_active: int
    total_pledged: int
    total_gap: int

class RegionSummaryResponse(BaseModel):
    id: int
    state_id: int
    lga_id: Optional[int] = None
    region_name: str
    region_type: str
    population: int
    target_ambulances: int
    total_active: int
    total_pending_verification: int
    total_under_maintenance: int
    total_pledged: int
    gap_count: int
    coverage_percentage: float
    color_band: str
    updated_at: datetime

    class Config:
        from_attributes = True

class PartnerContributionResponse(BaseModel):
    id: int
    plate_number: str
    make_model: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True
