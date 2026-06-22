from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.partners.models import PartnerUser
from app.partners.schemas import PartnerUserResponse, PartnerChangePassword
from app.schemas.common import ResponseBase, PaginatedResponse, PaginationMeta
from app.core.security import verify_password, get_password_hash
from datetime import datetime
from sqlalchemy import select, func, and_
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.ambulance_type import AmbulanceType
from app.models.hospital_type import HospitalType
from app.partners.schemas import PartnerDashboardStatsResponse, PartnerDashboardStatsData, DashboardEntityStats


router = APIRouter()

@router.get("/me", response_model=ResponseBase[PartnerUserResponse])
async def read_partner_me(
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
):
    """
    Get current partner user details using partner token
    """
    return {
        "success": True,
        "message": "Partner details successfully fetched",
        "data": current_partner
    }

@router.post("/change-password", response_model=ResponseBase)
async def change_partner_password(
    data: PartnerChangePassword,
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
):
    """
    Change partner password
    """
    if not verify_password(data.current_password, current_partner.hashed_password):
        raise HTTPException(status_code=400, detail={"message": "Incorrect current password", "error": "INVALID_PASSWORD"})
    
    current_partner.hashed_password = get_password_hash(data.new_password)
    db.add(current_partner)
    await db.commit()
    
    return {
        "success": True,
        "message": "Password changed successfully",
        "data": None
    }

from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy import or_, func

@router.get("/all", response_model=PaginatedResponse[PartnerUserResponse])
async def read_all_partners(
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
):
    """
    Get all partner users (partners and organizations). Only accessible by admins.
    Supports pagination and searching by name, email, or organization.
    """
    if current_partner.user_type not in ["SUPERADMINISTRATOR", "ADMINSEMSASUSER", "admin"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")

    conditions = []
    if search:
        search_pattern = f"%{search}%"
        conditions.append(or_(
            PartnerUser.first_name.ilike(search_pattern),
            PartnerUser.last_name.ilike(search_pattern),
            PartnerUser.email.ilike(search_pattern),
            PartnerUser.organisation_name.ilike(search_pattern)
        ))

    # Get total count
    count_query = select(func.count(PartnerUser.id))
    if conditions:
        count_query = count_query.where(*conditions)
    total_count = await db.scalar(count_query)

    # Get data
    query = select(PartnerUser)
    if conditions:
        query = query.where(*conditions)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    partners = result.scalars().all()
    
    return {
        "success": True,
        "message": "All partners fetched successfully",
        "data": partners,
        "meta": {
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    }

@router.get("/dashboard-stats", response_model=PartnerDashboardStatsResponse)
async def get_partner_dashboard_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_partner: PartnerUser = Depends(deps.get_current_partner_user) 
):
    """
    Get aggregated dashboard stats for ambulances and hospitals by their types, 
    with a month-over-month growth percentage for the current partner.
    """
    if not current_partner:
        raise HTTPException(status_code=400, detail={"message": "Partner not found", "error": "NOT_PARTNER"})

    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)
    if now.month == 1:
        last_month_start = datetime(now.year - 1, 12, 1)
    else:
        last_month_start = datetime(now.year, now.month - 1, 1)
        
    # Ambulance queries
    amb_query = (
        select(AmbulanceType.name, func.count(Ambulance.id))
        .select_from(AmbulanceType)
        .outerjoin(Ambulance, Ambulance.ambulance_type_id == AmbulanceType.id)
        .group_by(AmbulanceType.name)
    )
    amb_res = await db.execute(amb_query)
    amb_breakdown = {name: count for name, count in amb_res.all()}
    amb_total_res = await db.execute(select(func.count(Ambulance.id)))
    amb_total = amb_total_res.scalar() or 0
    
    amb_current_month = await db.execute(
        select(func.count(Ambulance.id))
        .where(Ambulance.date_added >= current_month_start)
    )
    amb_current_count = amb_current_month.scalar() or 0
    
    amb_last_month = await db.execute(
        select(func.count(Ambulance.id))
        .where(Ambulance.date_added >= last_month_start, Ambulance.date_added < current_month_start)
    )
    amb_last_count = amb_last_month.scalar() or 0
    
    amb_growth = 0.0
    if amb_last_count > 0:
        amb_growth = ((amb_current_count - amb_last_count) / amb_last_count) * 100.0
    elif amb_current_count > 0:
        amb_growth = 100.0
        
    amb_status_query = (
        select(Ambulance.status, Ambulance.active_status, func.count(Ambulance.id))
        .group_by(Ambulance.status, Ambulance.active_status)
    )
    amb_status_res = await db.execute(amb_status_query)
    raw_status_counts = amb_status_res.all()
    
    amb_status_breakdown = {
        "active": 0,
        "pending": 0,
        "out_of_service": 0,
        "under_maintenance": 0,
        "rejected": 0
    }
    
    for st, ast, cnt in raw_status_counts:
        if st and st.lower() == "rejected":
            amb_status_breakdown["rejected"] = amb_status_breakdown.get("rejected", 0) + cnt
        elif ast:
            mapped = ast.lower().replace(" ", "_")
            if mapped in amb_status_breakdown:
                amb_status_breakdown[mapped] += cnt
            else:
                amb_status_breakdown[mapped] = cnt
        
        
    # Hospital queries
    hosp_query = (
        select(HospitalType.name, func.count(Hospital.id))
        .select_from(HospitalType)
        .outerjoin(Hospital, Hospital.hospital_type_id == HospitalType.id)
        .group_by(HospitalType.name)
    )
    hosp_res = await db.execute(hosp_query)
    hosp_breakdown = {name: count for name, count in hosp_res.all()}
    hosp_total_res = await db.execute(select(func.count(Hospital.id)))
    hosp_total = hosp_total_res.scalar() or 0
    
    hosp_current_month = await db.execute(
        select(func.count(Hospital.id))
        .where(Hospital.date_added >= current_month_start)
    )
    hosp_current_count = hosp_current_month.scalar() or 0
    
    hosp_last_month = await db.execute(
        select(func.count(Hospital.id))
        .where(Hospital.date_added >= last_month_start, Hospital.date_added < current_month_start)
    )
    hosp_last_count = hosp_last_month.scalar() or 0
    
    hosp_growth = 0.0
    if hosp_last_count > 0:
        hosp_growth = ((hosp_current_count - hosp_last_count) / hosp_last_count) * 100.0
    elif hosp_current_count > 0:
        hosp_growth = 100.0
        
    hosp_status_query = (
        select(Hospital.status, func.count(Hospital.id))
        .group_by(Hospital.status)
    )
    hosp_status_res = await db.execute(hosp_status_query)
    raw_hosp_status_counts = {status: count for status, count in hosp_status_res.all() if status}
    
    def map_hosp_status(raw: str):
        low = raw.lower()
        if low == "approved":
            return "active"
        if low == "pending":
            return "pending"
        return low
        
    hosp_status_breakdown = {
        "active": 0,
        "pending": 0
    }
    
    for st, cnt in raw_hosp_status_counts.items():
        mapped = map_hosp_status(st)
        if mapped in hosp_status_breakdown:
            hosp_status_breakdown[mapped] += cnt
        else:
            hosp_status_breakdown[mapped] = hosp_status_breakdown.get(mapped, 0) + cnt
        
    return {
        "success": True,
        "message": "Dashboard stats fetched successfully",
        "data": {
            "ambulances": {
                "total": amb_total,
                "this_month": amb_current_count,
                "last_month": amb_last_count,
                "growth_percentage": round(amb_growth, 2),
                "breakdown": amb_breakdown,
                "status_breakdown": amb_status_breakdown
            },
            "hospitals": {
                "total": hosp_total,
                "this_month": hosp_current_count,
                "last_month": hosp_last_count,
                "growth_percentage": round(hosp_growth, 2),
                "breakdown": hosp_breakdown,
                "status_breakdown": hosp_status_breakdown
            }
        }
    }
