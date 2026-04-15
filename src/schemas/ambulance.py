from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from src.db.models.ambulance import AmbulanceStatus, AccreditationType

class AmbulanceBase(BaseModel):
    plate_number: str
    make_model: str
    year: int
    accreditation_type: AccreditationType
    fuel_type: Optional[str] = None
    capacity: int = 1
    state_id: int
    lga_id: int
    
    # Fleet Management Fields
    equipment: Optional[str] = None
    roadworthiness_expiry: Optional[date] = None
    insurance_expiry: Optional[date] = None

class AmbulanceCreate(AmbulanceBase):
    partner_id: Optional[int] = None

class AmbulanceUpdate(BaseModel):
    status: Optional[AmbulanceStatus] = None
    is_paused: Optional[bool] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    equipment: Optional[str] = None
    roadworthiness_expiry: Optional[date] = None
    insurance_expiry: Optional[date] = None
    facility_id: Optional[int] = None

class Ambulance(AmbulanceBase):
    id: int
    status: AmbulanceStatus
    is_paused: bool
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    partner_id: Optional[int] = None
    facility_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FleetFilter(BaseModel):
    accreditation_type: Optional[AccreditationType] = None
    status: Optional[AmbulanceStatus] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    partner_id: Optional[int] = None
    facility_id: Optional[int] = None

class BulkUploadRowReport(BaseModel):
    row_number: int
    plate_number: str
    is_valid: bool
    errors: List[str] = []
    data: Optional[dict] = None

class BulkUploadReport(BaseModel):
    total_rows: int
    passed_rows: int
    failed_rows: int
    reports: List[BulkUploadRowReport]

class AmbulanceAllocation(BaseModel):
    facility_id: int

class AmbulanceSearchResult(BaseModel):
    ambulance: Ambulance
    distance_meters: float

class DispatchBase(BaseModel):
    incident_id: int
    ambulance_id: int
    crew_id: int

class DispatchCreate(DispatchBase):
    pass

class Dispatch(DispatchBase):
    id: int
    dispatch_timestamp: datetime
    accepted_timestamp: Optional[datetime] = None
    completed_timestamp: Optional[datetime] = None
    total_distance: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)

class GPSHistoryCreate(BaseModel):
    ambulance_id: int
    incident_id: Optional[int] = None
    latitude: float
    longitude: float
    is_paused: bool = False
    incident_leg: Optional[str] = None # 'dispatch_to_scene', 'scene_to_etc', 'offline'
