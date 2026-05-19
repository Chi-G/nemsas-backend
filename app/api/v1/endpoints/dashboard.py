import calendar
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.monitoring import monitoring as crud_monitoring
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.incident import Incident
from app.models.lga import LGA
from app.models.state import State
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    noOfStates: int
    noOfMamiiLgas: int
    noOfIncidents: int
    noOfAmbulances: int
    noOfEmergendyCenters: int


class DashboardStatsResponse(BaseModel):
    success: bool = True
    message: str = "Dashboard data for Web fetched"
    data: DashboardStats
    totalCount: int = 1
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: Optional[str] = "0001-01-01T00:00:00"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(deps.get_db),
    state_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get statistics count for states, LGAs, incidents, ambulances, and emergency centers.
    - SUPERADMINISTRATOR & NEMSASADMIN see all statistics globally unless filtered by state_id.
    - SEMSAS users see statistics strictly scoped to their state (derived from JWT).
    - Ambulance and other users default to statistics scoped to their state if present.
    """
    role = getattr(current_user, "user_type", "")

    # Securely determine the effective state scoping
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN"]:
        effective_state_id = state_id
    elif role in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        effective_state_id = current_user.state_id
    else:
        effective_state_id = current_user.state_id

    # 1. Count States
    if effective_state_id is not None:
        no_of_states = 1
    else:
        stmt_states = select(func.count(State.id))
        no_of_states = (await db.execute(stmt_states)).scalar() or 0

    # 2. Count LGAs
    stmt_lgas = select(func.count(LGA.id))
    if effective_state_id is not None:
        stmt_lgas = stmt_lgas.where(LGA.state_id == effective_state_id)
    no_of_lgas = (await db.execute(stmt_lgas)).scalar() or 0

    # 3. Count Incidents
    stmt_incidents = select(func.count(Incident.id))
    if effective_state_id is not None:
        stmt_incidents = stmt_incidents.where(Incident.state_id == effective_state_id)
    no_of_incidents = (await db.execute(stmt_incidents)).scalar() or 0

    # 4. Count Ambulances
    stmt_ambulances = select(func.count(Ambulance.id))
    if effective_state_id is not None:
        stmt_ambulances = stmt_ambulances.where(Ambulance.state_id == effective_state_id)
    no_of_ambulances = (await db.execute(stmt_ambulances)).scalar() or 0

    # 5. Count Emergency Centers (Hospitals)
    stmt_hospitals = select(func.count(Hospital.id))
    if effective_state_id is not None:
        stmt_hospitals = stmt_hospitals.where(Hospital.state_id == effective_state_id)
    no_of_hospitals = (await db.execute(stmt_hospitals)).scalar() or 0

    return {
        "success": True,
        "message": "Dashboard data for Web fetched",
        "data": {
            "noOfStates": no_of_states,
            "noOfMamiiLgas": no_of_lgas,
            "noOfIncidents": no_of_incidents,
            "noOfAmbulances": no_of_ambulances,
            "noOfEmergendyCenters": no_of_hospitals,
        },
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00",
    }


@router.get("/monthly", response_model=Any)
async def get_dashboard_monthly(
    db: AsyncSession = Depends(deps.get_db),
    year: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Returns monthly analytics data for the dashboard graph (Jan–Dec).
    Aggregates monitoring evaluation records by month.
    Supports an optional `year` query parameter to filter by year.

    Example response:
        {
            "message": "Monthly data fetched successfully",
            "data": [
                {"month": "January", "noOfTransport": 0, "noOfMamiiLGAs": 33, ...},
                ...
            ]
        }
    """
    items = await crud_monitoring.get_monthly_aggregates(db, year=year)

    data = []
    for row in items:
        month_name = (
            calendar.month_name[row.month]
            if row.month and 1 <= row.month <= 12
            else "Unknown"
        )
        data.append({
            "month": month_name,
            "noOfTransport": int(row.noOfTransport or 0),
            "noOfMamiiLGAs": int(row.noOfMamiiLGAs or 0),
            "byTricycleAmbulance": int(row.byTricycleAmbulance or 0),
            "byNurtwDriver": int(row.byNurtwDriver or 0),
            "bls": int(row.bls or 0),
            "laborTransportation": int(row.laborTransportation or 0),
            "obstetricTransportation": int(row.obstetricTransportation or 0),
            "neonatalTransportation": int(row.neonatalTransportation or 0),
            "bemonc": int(row.bemonc or 0),
            "cemonc": int(row.cemonc or 0),
            "maternalMortalities": int(row.maternalMortalities or 0),
            "neonatalMortalities": int(row.neonatalMortalities or 0),
        })

    return {
        "message": "Monthly data fetched successfully",
        "data": data,
    }
