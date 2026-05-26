import calendar
from datetime import date, datetime, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.monitoring import monitoring as crud_monitoring
from app.schemas.monitoring import MonthlyAggregateResponse
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
# Helpers
# ---------------------------------------------------------------------------

def _incident_period_filter(stmt, period: str):
    """Apply a date range filter to an incident query based on period string."""
    today = date.today()
    if period == "this_year":
        start = datetime(today.year, 1, 1)
        stmt = stmt.where(Incident.date_added >= start)
    elif period == "this_month":
        start = datetime(today.year, today.month, 1)
        stmt = stmt.where(Incident.date_added >= start)
    elif period == "this_week":
        # Monday of the current week
        start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        stmt = stmt.where(Incident.date_added >= start)
    # "all" → no filter
    return stmt


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(deps.get_db),
    state_id: Optional[int] = None,
    period: str = Query(default="all", description="Filter incidents by period: all | this_month | this_week | this_year"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get statistics count for states, LGAs, incidents, ambulances, and emergency centers.

    - **period**: Filter incident count by `all` (default), `this_month`, `this_week`, `this_year`.
    - **noOfStates**: Distinct states that have at least one registered user.
    - **noOfMamiiLgas**: Distinct LGAs that have at least one registered user.
    - SUPERADMINISTRATOR & NEMSASADMIN see global stats unless `state_id` is provided.
    - State-scoped roles (SEMSAS*) see only their own state's data.
    """
    role = getattr(current_user, "user_type", "")

    # Determine effective state scoping
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN", "NEMSASUSER", "NATIONALVIEWER"]:
        effective_state_id = state_id
    else:
        effective_state_id = current_user.state_id

    # 1. Count distinct states: 29 globally, 1 if filtered, 0 if SEMSAS user (blocked)
    if "SEMSAS" in role or "STATE" in role:
        no_of_states = 0
    else:
        if effective_state_id is not None:
            no_of_states = 1
        else:
            no_of_states = 29

    # 2. Count distinct LGAs where ambulances (Mamii transport assets) are registered
    stmt_amb_lgas = select(distinct(Ambulance.lga_id)).where(Ambulance.lga_id.isnot(None))
    if effective_state_id is not None:
        stmt_amb_lgas = stmt_amb_lgas.where(Ambulance.state_id == effective_state_id)
    amb_lgas_res = await db.execute(stmt_amb_lgas)
    no_of_lgas = len(set(amb_lgas_res.scalars().all()))

    # 3. Count Incidents (with optional period filter)
    stmt_incidents = select(func.count(Incident.id))
    if effective_state_id is not None:
        stmt_incidents = stmt_incidents.where(Incident.state_id == effective_state_id)
    stmt_incidents = _incident_period_filter(stmt_incidents, period)
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


@router.get("/monthly", response_model=MonthlyAggregateResponse)
async def get_dashboard_monthly(
    db: AsyncSession = Depends(deps.get_db),
    year: Optional[int] = None,
    stateId: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Returns monthly analytics data for the dashboard graph.
    Only returns months up to the **current month** for the current year,
    so future months are never shown in the response.

    Supports an optional `year` query parameter to filter by a specific year.
    Supports an optional `stateId` query parameter to filter by state.
    For state-scoped roles, this defaults to the user's assigned state.
    """
    role = getattr(current_user, "user_type", "")

    # Determine effective state scoping
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN", "NEMSASUSER", "NATIONALVIEWER"]:
        effective_state_id = stateId
    else:
        effective_state_id = current_user.state_id

    today = date.today()
    effective_year = year or today.year

    items = await crud_monitoring.get_monthly_aggregates(db, year=effective_year, state_id=effective_state_id)

    data = []
    for row in items:
        if not row.month or not (1 <= row.month <= 12):
            continue

        # For the current year, suppress future months
        if effective_year == today.year and row.month > today.month:
            continue

        month_name = calendar.month_name[row.month]
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
