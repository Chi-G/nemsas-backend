from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import PaginationMeta

class RecentActivityItem(BaseModel):
    title: str
    desc: str
    metaData: Dict[str, Any]
    meta_data_hyphen: Dict[str, Any] = Field(..., alias="meta-data")
    status: str
    createdAt: datetime
    date: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class ClaimsOverview(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    paid: int = 0
    total: int = 0
    totalAmount: float = 0.0          # SUM of all claims total_price
    etcTotalAmount: float = 0.0       # SUM of ETC claims total_price
    ambulanceTotalAmount: float = 0.0 # SUM of Ambulance claims total_price

class IncidentsOverview(BaseModel):
    created: int = 0
    reported: int = 0
    dispatched: int = 0
    accepted: int = 0
    enRoute: int = Field(0, alias="enRoute")
    atScene: int = Field(0, alias="atScene")
    patientLoaded: int = Field(0, alias="patientLoaded")
    enRouteToEtc: int = Field(0, alias="enRouteToEtc")
    arrivedAtEtc: int = Field(0, alias="arrivedAtEtc")
    completed: int = 0
    closed: int = 0
    total: int = 0
    averageResponseTime: int = 0


    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class MobileDashboardData(BaseModel):
    claimsOverview: ClaimsOverview
    incidentsOverview: IncidentsOverview
    recentActivity: List[RecentActivityItem]
    pagination: PaginationMeta

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class MobileDashboardResponse(BaseModel):
    success: bool = True
    message: str = "Mobile dashboard data retrieved successfully"
    data: MobileDashboardData
