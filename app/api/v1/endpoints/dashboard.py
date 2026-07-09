import calendar
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import distinct, func, select, desc 
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.monitoring import monitoring as crud_monitoring
from app.schemas.monitoring import MonthlyAggregateResponse
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.incident import Incident 
from app.models.claim import Claim 
from app.models.patient import Patient
from app.models.lga import LGA
from app.models.state import State
from app.models.user import User
from app.schemas.dashboard import (
    MobileDashboardResponse,
    MobileDashboardActivitiesResponse
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    noOfStates: int
    noOfMamiiLgas: int
    noOfIncidents: int
    noOfAmbulanceRuns: int
    noOfTreatments: int
    
    # ETC-specific stats
    noOfPatients: Optional[int] = None
    lastMonthIncidents: Optional[int] = None
    thisMonthIncidents: Optional[int] = None
    lastMonthPatients: Optional[int] = None
    thisMonthPatients: Optional[int] = None
    thisMonthAmbulanceRuns: Optional[int] = None
    lastMonthAmbulanceRuns: Optional[int] = None
    thisMonthTreatments: Optional[int] = None
    lastMonthTreatments: Optional[int] = None


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
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN", "NEMSASUSER", "NATIONALVIEWER",'PERMSEC']:
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

    # 4. Count Ambulance Runs
    stmt_ambulance_runs = select(func.count(Incident.id)).where(
        Incident.ambulance_id.isnot(None),
        Incident.event_status_type.isnot(None)
    )
    if effective_state_id is not None:
        stmt_ambulance_runs = stmt_ambulance_runs.where(Incident.state_id == effective_state_id)
    stmt_ambulance_runs = _incident_period_filter(stmt_ambulance_runs, period)
    no_of_ambulance_runs = (await db.execute(stmt_ambulance_runs)).scalar() or 0

    # 5. Count Emergency Treatments in Facilities
    stmt_treatments = select(func.count(Claim.id)).join(Incident).where(Claim.etc_claim_status != "Not Applicable")
    if effective_state_id is not None:
        stmt_treatments = stmt_treatments.where(Incident.state_id == effective_state_id)
    if period == "this_year":
        stmt_treatments = stmt_treatments.where(Incident.date_added >= datetime(date.today().year, 1, 1, tzinfo=timezone.utc))
    elif period == "this_month":
        stmt_treatments = stmt_treatments.where(Incident.date_added >= datetime(date.today().year, date.today().month, 1, tzinfo=timezone.utc))
    elif period == "this_week":
        start_week = datetime.combine(date.today() - timedelta(days=date.today().weekday()), datetime.min.time()).replace(tzinfo=timezone.utc)
        stmt_treatments = stmt_treatments.where(Incident.date_added >= start_week)
    no_of_treatments = (await db.execute(stmt_treatments)).scalar() or 0

    # Calculate global trends
    today = date.today()
    this_month_start = datetime(today.year, today.month, 1, tzinfo=timezone.utc)
    if today.month == 1:
        last_month_start = datetime(today.year - 1, 12, 1, tzinfo=timezone.utc)
    else:
        last_month_start = datetime(today.year, today.month - 1, 1, tzinfo=timezone.utc)
    last_month_end = this_month_start

    # Trend: Ambulance Runs
    stmt_amb_this = select(func.count(Incident.id)).where(
        Incident.ambulance_id.isnot(None), Incident.event_status_type.isnot(None), Incident.date_added >= this_month_start)
    stmt_amb_last = select(func.count(Incident.id)).where(
        Incident.ambulance_id.isnot(None), Incident.event_status_type.isnot(None), Incident.date_added >= last_month_start, Incident.date_added < last_month_end)
    if effective_state_id is not None:
        stmt_amb_this = stmt_amb_this.where(Incident.state_id == effective_state_id)
        stmt_amb_last = stmt_amb_last.where(Incident.state_id == effective_state_id)
    this_month_ambulance_runs = (await db.execute(stmt_amb_this)).scalar() or 0
    last_month_ambulance_runs = (await db.execute(stmt_amb_last)).scalar() or 0

    # Trend: Treatments
    stmt_treat_this = select(func.count(Claim.id)).join(Incident).where(Claim.etc_claim_status != "Not Applicable", Incident.date_added >= this_month_start)
    stmt_treat_last = select(func.count(Claim.id)).join(Incident).where(Claim.etc_claim_status != "Not Applicable", Incident.date_added >= last_month_start, Incident.date_added < last_month_end)
    if effective_state_id is not None:
        stmt_treat_this = stmt_treat_this.where(Incident.state_id == effective_state_id)
        stmt_treat_last = stmt_treat_last.where(Incident.state_id == effective_state_id)
    this_month_treatments = (await db.execute(stmt_treat_this)).scalar() or 0
    last_month_treatments = (await db.execute(stmt_treat_last)).scalar() or 0

    response_data = {
        "noOfStates": no_of_states,
        "noOfMamiiLgas": no_of_lgas,
        "noOfIncidents": no_of_incidents,
        "noOfAmbulanceRuns": no_of_ambulance_runs,
        "noOfTreatments": no_of_treatments,
        "thisMonthAmbulanceRuns": this_month_ambulance_runs,
        "lastMonthAmbulanceRuns": last_month_ambulance_runs,
        "thisMonthTreatments": this_month_treatments,
        "lastMonthTreatments": last_month_treatments,
    }

    # 6. Additional Stats for EMERGENCYTREATMENTUSER
    if role == "EMERGENCYTREATMENTUSER":
        etc_id = getattr(current_user, "etc_id", None) or getattr(current_user, "emergency_treatment_center_id", None)
        if etc_id is not None:
            # Overwrite total incidents specifically for this ETC
            stmt_etc_incidents = select(func.count(Incident.id)).where(Incident.etc_id == etc_id)
            stmt_etc_incidents = _incident_period_filter(stmt_etc_incidents, period)
            response_data["noOfIncidents"] = (await db.execute(stmt_etc_incidents)).scalar() or 0

            # Total Patients
            stmt_patients = select(func.count(Patient.id)).join(Incident, Patient.incident_id == Incident.id).where(Patient.etc_id == etc_id)
            stmt_patients = _incident_period_filter(stmt_patients, period)
            response_data["noOfPatients"] = (await db.execute(stmt_patients)).scalar() or 0

            # The dates are already computed globally above
            
            # Incidents: This month & Last month
            stmt_inc_this = select(func.count(Incident.id)).where(Incident.etc_id == etc_id, Incident.date_added >= this_month_start)
            stmt_inc_last = select(func.count(Incident.id)).where(Incident.etc_id == etc_id, Incident.date_added >= last_month_start, Incident.date_added < last_month_end)
            
            response_data["thisMonthIncidents"] = (await db.execute(stmt_inc_this)).scalar() or 0
            response_data["lastMonthIncidents"] = (await db.execute(stmt_inc_last)).scalar() or 0
            
            # Patients: This month & Last month
            stmt_pat_this = select(func.count(Patient.id)).join(Incident, Patient.incident_id == Incident.id).where(Patient.etc_id == etc_id, Incident.date_added >= this_month_start)
            stmt_pat_last = select(func.count(Patient.id)).join(Incident, Patient.incident_id == Incident.id).where(Patient.etc_id == etc_id, Incident.date_added >= last_month_start, Incident.date_added < last_month_end)
            
            response_data["thisMonthPatients"] = (await db.execute(stmt_pat_this)).scalar() or 0
            response_data["lastMonthPatients"] = (await db.execute(stmt_pat_last)).scalar() or 0

    return {
        "success": True,
        "message": "Dashboard data for Web fetched",
        "data": response_data,
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
    if role in ["SUPERADMINISTRATOR", "NEMSASADMIN", "NEMSASUSER", "NATIONALVIEWER",'PERMSEC']:
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
            "bls": int(row.bls or 0),
            "als": int(row.als or 0),
            "helicopters": int(row.helicopters or 0),
            "communityVolunteers": int(row.communityVolunteers or 0),
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


# ---------------------------------------------------------------------------
# Mobile Dashboard & Recent Activity
# ---------------------------------------------------------------------------

class CustomRequiredIdModel(BaseModel):
    id: int


async def _build_mobile_dashboard_data(
    db: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 8,
    activities_only: bool = False
) -> dict:
    # Scope by ambulance_id instead of state_id for mobile users
    effective_ambulance_id = current_user.ambulance_id

    # If only fetching activities, skip overview queries
    claims_overview = {"total": 0, "approved": 0, "rejected": 0, "pending": 0}
    incidents_overview = {"reported": 0, "dispatched": 0, "completed": 0, "total": 0, "averageResponseTime": 6}

    if effective_ambulance_id is None:
        response_data = {
            "recentActivity": [],
            "pagination": {"total": 0, "skip": skip, "limit": limit}
        }
        if not activities_only:
            response_data["claimsOverview"] = claims_overview
            response_data["incidentsOverview"] = incidents_overview
        return {
            "success": True,
            "message": "No assigned ambulance",
            "data": response_data
        }

    if not activities_only:
        # 1. Claims Overview counts
        stmt_claims = select(Claim.ambulance_claim_status, func.count(Claim.id))
        if effective_ambulance_id is not None:
            stmt_claims = stmt_claims.join(Claim.incident).where(Incident.ambulance_id == effective_ambulance_id)
        stmt_claims = stmt_claims.group_by(Claim.ambulance_claim_status)
        res_claims = await db.execute(stmt_claims)
    
        claims_counts = {}
        for row in res_claims.all():
            status_val = row[0]
            count_val = row[1]
            if status_val:
                normalized = status_val.value.strip().lower() if hasattr(status_val, "value") else str(status_val).strip().lower()
                claims_counts[normalized] = claims_counts.get(normalized, 0) + count_val
            
        claims_pending = (
            claims_counts.get("pending", 0)
            + claims_counts.get("new", 0)
        )
        claims_approved = (
            claims_counts.get("approved", 0)
            + claims_counts.get("endorsed", 0)
        )
        claims_rejected = claims_counts.get("rejected", 0)
        claims_paid = claims_counts.get("paid", 0)
        claims_total = sum(claims_counts.values())

        # Calculate claim amounts
        stmt_claims_amount = select(
            func.sum(Claim.total_price).label('totalAmount'),
            func.sum(func.coalesce(Claim.total_price, 0)).filter(Incident.etc_id != None).label('etcTotalAmount'),
            func.sum(func.coalesce(Claim.total_price, 0)).filter(Incident.ambulance_id != None).label('ambulanceTotalAmount')
        ).join(Claim.incident)
        if effective_ambulance_id is not None:
            stmt_claims_amount = stmt_claims_amount.where(Incident.ambulance_id == effective_ambulance_id)
        res_claims_amount = await db.execute(stmt_claims_amount)
        row_claims_amount = res_claims_amount.first()
    
        total_amount = float(getattr(row_claims_amount, 'totalAmount', 0.0) or 0.0) if row_claims_amount else 0.0
        etc_total_amount = float(getattr(row_claims_amount, 'etcTotalAmount', 0.0) or 0.0) if row_claims_amount else 0.0
        ambulance_total_amount = float(getattr(row_claims_amount, 'ambulanceTotalAmount', 0.0) or 0.0) if row_claims_amount else 0.0

        claims_overview = {
            "pending": claims_pending,
            "approved": claims_approved,
            "rejected": claims_rejected,
            "paid": claims_paid,
            "total": claims_total,
            "totalAmount": total_amount,
            "etcTotalAmount": etc_total_amount,
            "ambulanceTotalAmount": ambulance_total_amount
        }

        # 2. Incidents Overview counts
        stmt_incidents = select(Incident.incident_status_type, func.count(Incident.id))
        if effective_ambulance_id is not None:
            stmt_incidents = stmt_incidents.where(Incident.ambulance_id == effective_ambulance_id)
        stmt_incidents = stmt_incidents.group_by(Incident.incident_status_type)
        res_incidents = await db.execute(stmt_incidents)
    
        incidents_counts = {}
        for row in res_incidents.all():
            status_val = row[0]
            count_val = row[1]
            if status_val:
                normalized = status_val.value.strip().lower() if hasattr(status_val, "value") else str(status_val).strip().lower()
                incidents_counts[normalized] = incidents_counts.get(normalized, 0) + count_val

        incidents_overview = {
            "created": incidents_counts.get("created", 0),
            "reported": incidents_counts.get("reported", 0),
            "dispatched": incidents_counts.get("dispatched", 0),
            "accepted": incidents_counts.get("accepted", 0),
            "enRoute": incidents_counts.get("en route", 0),
            "atScene": incidents_counts.get("at scene", 0),
            "patientLoaded": incidents_counts.get("patient loaded", 0),
            "enRouteToEtc": incidents_counts.get("en route to etc", 0),
            "arrivedAtEtc": incidents_counts.get("arrived at etc", 0),
            "completed": incidents_counts.get("completed", 0),
            "closed": incidents_counts.get("closed", 0),
            "total": sum(incidents_counts.values()),
            "averageResponseTime": 6
        }

    # Helper for relative time in recent activities
    def get_relative_time(dt: datetime) -> str:
        if not dt:
            return ""
        now = datetime.now(timezone.utc)
        dt_aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        diff = now - dt_aware
        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds // 3600)}h ago"
        else:
            return f"{int(seconds // 86400)}d ago"

    # 3. Recent Activity List
    limit_val = skip + limit
    
    # Query incidents
    stmt_inc = select(Incident).order_by(desc(Incident.date_added))
    if effective_ambulance_id is not None:
        stmt_inc = stmt_inc.where(Incident.ambulance_id == effective_ambulance_id)
    stmt_inc = stmt_inc.limit(limit_val)
    res_inc = await db.execute(stmt_inc)
    inc_list = res_inc.scalars().all()

    # Query claims
    stmt_cl = select(Claim).order_by(desc(Claim.created_at))
    if effective_ambulance_id is not None:
        stmt_cl = stmt_cl.join(Claim.incident).where(Incident.ambulance_id == effective_ambulance_id)
    stmt_cl = stmt_cl.limit(limit_val)
    res_cl = await db.execute(stmt_cl)
    cl_list = res_cl.scalars().all()

    # Map activities
    activities = []
    for inc in inc_list:
        status_val = inc.event_status_type or inc.incident_status_type or "Reported"
        status_str = status_val.value if hasattr(status_val, "value") else str(status_val)
        
        if status_str.lower() == "reported":
            title = "New incident reported"
        elif status_str.lower() in ["completed", "closed"]:
            title = "Road accident incident resolved"
        else:
            title = f"Incident {status_str}"

        location_str = inc.incident_location or inc.street or inc.district_ward or "Unknown Location"
        activity_desc = location_str
        
        activities.append({
            "title": title,
            "desc": activity_desc,
            "metaData": {
                "incidentId": inc.id,
                "serialNo": inc.serial_no,
                "type": "incident",
                "location": location_str
            },
            "meta-data": {
                "incidentId": inc.id,
                "serialNo": inc.serial_no,
                "type": "incident",
                "location": location_str
            },
            "status": status_str,
            "createdAt": inc.date_added or datetime.min.replace(tzinfo=timezone.utc),
            "date": get_relative_time(inc.date_added)
        })

    for cl in cl_list:
        status_val = cl.ambulance_claim_status or "New"
        status_str = status_val.value if hasattr(status_val, "value") else str(status_val)
        
        if status_str.lower() == "approved":
            title = f"Claim #{cl.id} approved"
            activity_desc = f"Patient: {cl.patient_name or 'Unknown'}"
        elif status_str.lower() == "rejected":
            title = f"Claim #{cl.id} rejected"
            activity_desc = cl.rejection_reason or "Incomplete documents submitted"
        elif status_str.lower() in ["pending", "new", "endorsed"]:
            title = f"Claim #{cl.id} pending review"
            activity_desc = "Awaiting hospital verification"
        else:
            title = f"Claim #{cl.id} {status_str.lower()}"
            activity_desc = f"Patient: {cl.patient_name or 'Unknown'}"

        activities.append({
            "title": title,
            "desc": activity_desc,
            "metaData": {
                "claimId": cl.id,
                "incidentId": cl.incident_id,
                "type": "claim",
                "patientName": cl.patient_name
            },
            "meta-data": {
                "claimId": cl.id,
                "incidentId": cl.incident_id,
                "type": "claim",
                "patientName": cl.patient_name
            },
            "status": status_str,
            "createdAt": cl.created_at or datetime.min.replace(tzinfo=timezone.utc),
            "date": get_relative_time(cl.created_at)
        })

    # Helper to sort datetimes with potential None/tz mismatches
    def normalize_dt(dt):
        if dt is None:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    activities.sort(key=lambda x: normalize_dt(x["createdAt"]), reverse=True)
    paginated_activities = activities[skip : skip + limit]

    # Query totals
    stmt_total_inc = select(func.count(Incident.id))
    if effective_ambulance_id is not None:
        stmt_total_inc = stmt_total_inc.where(Incident.ambulance_id == effective_ambulance_id)
    total_inc = (await db.execute(stmt_total_inc)).scalar() or 0

    stmt_total_cl = select(func.count(Claim.id))
    if effective_ambulance_id is not None:
        stmt_total_cl = stmt_total_cl.join(Claim.incident).where(Incident.ambulance_id == effective_ambulance_id)
    total_cl = (await db.execute(stmt_total_cl)).scalar() or 0

    total_activities = total_inc + total_cl

    response_data = {
        "recentActivity": paginated_activities,
        "pagination": {
            "total": total_activities,
            "skip": skip,
            "limit": limit
        }
    }

    if not activities_only:
        response_data["claimsOverview"] = claims_overview
        response_data["incidentsOverview"] = incidents_overview

    return {
        "success": True,
        "message": "Mobile dashboard data retrieved successfully",
        "data": response_data
    }


@router.get("/mobile", response_model=MobileDashboardResponse)
async def get_mobile_dashboard(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get mobile dashboard statistics (claims overview & incidents overview)
    and a paginated list of recent activity (merging claims and incidents).
    """
    return await _build_mobile_dashboard_data(
        db=db,
        current_user=current_user,
        skip=0,
        limit=8,
        activities_only=False
    )

@router.get("/mobile/activities", response_model=MobileDashboardActivitiesResponse)
async def get_mobile_dashboard_activities(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get paginated recent activity for the mobile dashboard.
    """
    return await _build_mobile_dashboard_data(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        activities_only=True
    )

@router.get("/dashboardMobile", response_model=MobileDashboardResponse)
async def get_dashboard_mobile_alias(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Alias GET for dashboardMobile."""
    return await _build_mobile_dashboard_data(
        db=db,
        current_user=current_user,
        skip=0,
        limit=8,
        activities_only=False
    )

@router.post("/dashboardMobile", response_model=MobileDashboardResponse)
async def post_dashboard_mobile(
    body: Optional[CustomRequiredIdModel] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Legacy POST dashboardMobile handler matching C# specification.
    """
    return await _build_mobile_dashboard_data(
        db=db,
        current_user=current_user,
        skip=0,
        limit=8,
        activities_only=False
    )

from sqlalchemy import extract, case

@router.get("/chart")
async def get_dashboard_chart(
    view: str = Query(..., description="View type: ambulance runs, emergency types, claims"),
    stateId: Optional[int] = None,
    year: Optional[str] = None,
    emergencyType: Optional[str] = None,
    claimsType: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get aggregated data for the NEMSAS Bar Chart.
    Supports filtering by view, stateId, year, emergencyType, and claimsType.
    """
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    target_year = int(year) if year else datetime.now(timezone.utc).year
    
    def init_months():
        return {m: 0 for m in range(1, 13)}

    datasets = []
    view_lower = view.lower()
    
    if view_lower in ["ambulance", "ambulance runs", "ambulance & response"]:
        from app.models.ambulance_type import AmbulanceType
        from app.models.incident_type import IncidentType
        
        stmt = select(
            extract('month', Incident.date_added).label('month'),
            func.count(Incident.id).label('incidents'),
            func.count(case((Incident.ambulance_id.isnot(None) & Incident.event_status_type.isnot(None), 1))).label('ambulance_runs'),
            func.count(case((AmbulanceType.name.ilike('%ALS%'), 1))).label('als'),
            func.count(case((AmbulanceType.name.ilike('%BLS%'), 1))).label('bls'),
            func.count(case((AmbulanceType.name.ilike('%Tricycle%'), 1))).label('tricycle'),
            func.count(case((AmbulanceType.name.ilike('%Boat%'), 1))).label('boat'),
            func.count(case((AmbulanceType.name.ilike('%Helicopter%'), 1))).label('helicopter'),
        ).outerjoin(Ambulance, Incident.ambulance_id == Ambulance.id)\
         .outerjoin(AmbulanceType, Ambulance.ambulance_type_id == AmbulanceType.id)\
         .where(extract('year', Incident.date_added) == target_year)
         
        if emergencyType and emergencyType != "All":
            stmt = stmt.join(IncidentType, Incident.incident_category_id == IncidentType.id).where(IncidentType.name == emergencyType)
         
        if stateId:
            stmt = stmt.where(Incident.state_id == stateId)
            
        stmt = stmt.group_by(extract('month', Incident.date_added))
        
        res = await db.execute(stmt)
        rows = res.all()
        
        data = {
            'Incidents': init_months(),
            'Ambulance runs': init_months(),
            'ALS': init_months(),
            'BLS': init_months(),
            'Tricycle': init_months(),
            'Boat': init_months(),
            'Helicopter': init_months(),
        }
        
        for row in rows:
            if row.month is None: continue
            m = int(row.month)
            if 1 <= m <= 12:
                data['Incidents'][m] = row.incidents or 0
                data['Ambulance runs'][m] = row.ambulance_runs or 0
                data['ALS'][m] = row.als or 0
                data['BLS'][m] = row.bls or 0
                data['Tricycle'][m] = row.tricycle or 0
                data['Boat'][m] = row.boat or 0
                data['Helicopter'][m] = row.helicopter or 0
                
        # Incidents first, then Ambulance runs
        order = ['Incidents', 'Ambulance runs', 'ALS', 'BLS', 'Tricycle', 'Boat', 'Helicopter']
        datasets = [
            {"name": k, "data": [data[k][m] for m in range(1, 13)]} for k in order
        ]

    elif view_lower in ["emergency", "emergency types", "incidents"]:
        # If "All" or none is selected, return total incidents grouped by month
        from app.models.incident_type import IncidentType

        stmt = select(
            extract('month', Incident.date_added).label('month'),
            func.count(Incident.id).label('count')
        ).where(extract('year', Incident.date_added) == target_year)

        name_label = "All Incidents"
        if emergencyType and emergencyType != "All":
            name_label = emergencyType
            stmt = stmt.join(IncidentType, Incident.incident_category_id == IncidentType.id)\
                       .where(IncidentType.name == emergencyType)
        
        if stateId:
            stmt = stmt.where(Incident.state_id == stateId)
            
        stmt = stmt.group_by(extract('month', Incident.date_added))
        res = await db.execute(stmt)
        
        month_data = init_months()
        for row in res.all():
            if row.month is None: continue
            m = int(row.month)
            if 1 <= m <= 12:
                month_data[m] = row.count or 0
                
        datasets = [
            {"name": name_label, "data": [month_data[m] for m in range(1, 13)]}
        ]

    elif view_lower == "claims":
        from app.models.claim import Claim
        from app.models.incident_type import IncidentType

        if claimsType == "ambulance":
            status_col = Claim.ambulance_claim_status
        else:
            status_col = Claim.etc_claim_status

        stmt = select(
            extract('month', Incident.date_added).label('month'),
            func.count(Claim.id).label('total'),
            func.count(case((status_col.ilike('%Pending%') | status_col.ilike('%New%'), 1))).label('pending'),
            func.count(case((status_col.ilike('%Endorsed%'), 1))).label('endorsed'),
            func.count(case((status_col.ilike('%Approved%'), 1))).label('approved'),
            func.count(case((status_col.ilike('%Rejected%'), 1))).label('rejected'),
        ).join(Incident, Claim.incident_id == Incident.id)\
         .where(extract('year', Incident.date_added) == target_year)\
         .where(status_col != "Not Applicable")

        if claimsType == "ambulance":
            stmt = stmt.where(Incident.ambulance_id.isnot(None))
        else:
            stmt = stmt.where(Incident.etc_id.isnot(None))
        
        if emergencyType and emergencyType != "All":
            stmt = stmt.join(IncidentType, Incident.incident_category_id == IncidentType.id).where(IncidentType.name == emergencyType)

        if stateId:
            stmt = stmt.where(Incident.state_id == stateId)
            
        stmt = stmt.group_by(extract('month', Incident.date_added))
        res = await db.execute(stmt)
        
        data = {
            'Total': init_months(),
            'Pending': init_months(),
            'Endorsed': init_months(),
            'Approved': init_months(),
            'Rejected': init_months(),
        }
        for row in res.all():
            if row.month is None: continue
            m = int(row.month)
            if 1 <= m <= 12:
                data['Total'][m] = row.total or 0
                data['Pending'][m] = row.pending or 0
                data['Endorsed'][m] = row.endorsed or 0
                data['Approved'][m] = row.approved or 0
                data['Rejected'][m] = row.rejected or 0
                
        order = ['Total', 'Pending', 'Endorsed', 'Approved', 'Rejected']
        datasets = [
            {"name": k, "data": [data[k][m] for m in range(1, 13)]} for k in order
        ]

    return {
        "success": True,
        "message": "Chart data fetched successfully",
        "data": {
            "categories": months,
            "series": datasets
        }
    }
