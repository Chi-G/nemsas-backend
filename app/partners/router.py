from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
import uuid

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.email import send_verification_email, send_password_reset_email
from app.partners.models import PartnerUser, PartnerPledge, PartnerFacility, PartnerAmbulance
from app.partners.schemas import (
    PartnerRegister, PartnerLogin, PartnerToken, PartnerUserResponse,
    PartnerVerifyAccount, PartnerResendCode, PartnerForgotPassword, PartnerResetPassword,
    PartnerPledgeCreate, PartnerPledgeResponse, PartnerPledgesListResponse,
    PartnerFacilityCreate, PartnerFacilityResponse, PartnerFacilitiesListResponse,
    PartnerAmbulanceCreate, PartnerAmbulanceResponse, PartnerAmbulancesListResponse,
    PartnerDashboardResponse, IdNameSchema, AddedBySchema,
    PledgesListContainer, PledgesListData, PledgeSummary,
    FacilitiesContainer, PaginationSchema,
    AmbulancesListContainer, AmbulancesContainer, AmbulanceListSummary,
    AmbBasicInformation, AmbTechnicalSpecification, AmbEquipmentInventory, AmbComplianceAndDocumentation, AmbStatus,
    DashboardOverviewContainer, OverviewListData, OverviewCardsContainer,
    AmbOverviewItem, OverviewCardAmbulance, OverviewCardHealthFacility, OverviewCardRequired, OverviewCardGaps
)
from app.partners.crud import (
    partner_user as crud_partner_user,
    partner_pledge as crud_partner_pledge,
    partner_facility as crud_partner_facility,
    partner_ambulance as crud_partner_ambulance
)

router = APIRouter()

# --- Helpers ---
def map_id_name(obj) -> Optional[IdNameSchema]:
    if not obj:
        return None
    name_val = getattr(obj, "name", "")
    return IdNameSchema(id=obj.id, name=name_val)

def map_added_by(user: PartnerUser) -> AddedBySchema:
    return AddedBySchema(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name or "",
        email=user.email,
        phone_number=user.phone_number,
        organisation_name=user.organisation_name,
        user_type=user.user_type,
        created_at=user.created_at
    )

# --- Auth ---
@router.post("/auth/register", response_model=PartnerUserResponse)
async def register(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: PartnerRegister,
    background_tasks: BackgroundTasks
) -> Any:
    """Register a new partner user and send verification email."""
    existing_user = await crud_partner_user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A partner user with this email already exists."
        )
    user = await crud_partner_user.create(db, obj_in=user_in)
    
    if user.verification_code:
        background_tasks.add_task(
            send_verification_email,
            to_email=user.email,
            name=f"{user.first_name} {user.last_name}",
            code=user.verification_code
        )
    return user

@router.post("/auth/verify-account")
async def verify_account(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: PartnerVerifyAccount
) -> Any:
    """Verify partner user account using code."""
    user = await crud_partner_user.get_by_email(db, email=body.email)
    if not user:
        raise HTTPException(status_code=404, detail="Partner user not found.")
        
    if user.is_verified:
        return {"success": True, "message": "Account already verified."}

    if user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    if user.verification_code_expires_at:
        expires_at = user.verification_code_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc) 
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"success": True, "message": "Account successfully verified."}

@router.post("/auth/resend-code")
async def resend_verification_code(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: PartnerResendCode,
    background_tasks: BackgroundTasks
) -> Any:
    """Resend verification code to partner email."""
    user = await crud_partner_user.get_by_email(db, email=body.email)
    if not user:
        raise HTTPException(status_code=404, detail="Partner user not found.")
        
    if user.is_verified:
        return {"success": True, "message": "Account already verified."}

    import random
    user.verification_code = str(random.randint(100000, 999999))
    user.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(seconds=90)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(
        send_verification_email,
        to_email=user.email,
        name=f"{user.first_name} {user.last_name}",
        code=user.verification_code
    )
    return {"success": True, "message": "Verification code successfully resent."}

@router.post("/auth/forgot-password")
async def forgot_password(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: PartnerForgotPassword,
    background_tasks: BackgroundTasks
) -> Any:
    """Send password reset code to partner email."""
    user = await crud_partner_user.get_by_email(db, email=body.email)
    if not user:
        raise HTTPException(status_code=404, detail="Partner user not found.")

    import random
    user.reset_password_code = str(random.randint(100000, 999999))
    user.reset_password_code_expires_at = datetime.now(timezone.utc) + timedelta(seconds=90)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(
        send_password_reset_email,
        to_email=user.email,
        name=f"{user.first_name} {user.last_name}",
        code=user.reset_password_code
    )
    return {"success": True, "message": "Password reset code successfully sent."}

@router.post("/auth/reset-password")
async def reset_password(
    *,
    db: AsyncSession = Depends(deps.get_db),
    body: PartnerResetPassword
) -> Any:
    """Reset partner user password using code."""
    user = await crud_partner_user.get_by_email(db, email=body.email)
    if not user:
        raise HTTPException(status_code=404, detail="Partner user not found.")

    if not user.reset_password_code or user.reset_password_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid password reset code.")

    if user.reset_password_code_expires_at:
        expires_at = user.reset_password_code_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new one.")

    user.hashed_password = security.get_password_hash(body.new_password)
    user.reset_password_code = None
    user.reset_password_code_expires_at = None
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"success": True, "message": "Password successfully reset."}

@router.post("/auth/login", response_model=PartnerToken)
async def login(
    *,
    db: AsyncSession = Depends(deps.get_db),
    login_data: PartnerLogin
) -> Any:
    """Authenticate partner user and return JWT token."""
    user = await crud_partner_user.get_by_email(db, email=login_data.email)
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account email is not verified. Please verify your email first."
        )
    
    # Generate tokens, setting role="PARTNER_CONNECT" or similar
    access_token = security.create_access_token(user.id, role="PARTNER_CONNECT")
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "status": "success",
        "message": "Login successful",
        "expires_in": expires_in,
        "user": user
    }

@router.get("/auth/me", response_model=PartnerUserResponse)
async def get_me(
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Get current partner user details."""
    return current_user

# --- Dashboard / Overview ---
@router.get("/dashboard", response_model=PartnerDashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 10,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Get NEMSAS Connect Dashboard overview list and card statistics."""
    skip = (page - 1) * pageSize
    
    # 1. Fetch Ambulances Overview List
    ambulances, total_amb = await crud_partner_ambulance.get_multi_with_count(
        db, skip=skip, limit=pageSize, added_by_id=current_user.id
    )
    
    over_view_data = []
    for amb in ambulances:
        over_view_data.append(AmbOverviewItem(
            id=amb.ambulance_id_str,
            plateNumber=amb.plate_number,
            driverName=amb.driver_name,
            state=amb.state.name if amb.state else "",
            lga=amb.lga.name if amb.lga else "",
            ward=amb.ward.name if amb.ward else "",
            facility=amb.facility.name if amb.facility else "",
            isOutForMaintenance=amb.is_out_for_maintenance,
            isOutOfService=amb.is_out_of_service,
            vehicleOwnershipType=amb.vehicle_ownership_type,
            status=amb.status,
            createdAt=amb.created_at.date().isoformat() if amb.created_at else "",
            updatedAt=amb.updated_at.date().isoformat() if amb.updated_at else ""
        ))
        
    pagination = PaginationSchema(
        total=total_amb,
        page=page,
        limit=pageSize
    )
    
    overview_list = OverviewListData(
        data=over_view_data,
        pagination=pagination
    )
    
    # 2. Card Statistics
    # Ambulance overview card
    amb_counts = await crud_partner_ambulance.get_summary_counts(db, added_by_id=current_user.id)
    card_amb = OverviewCardAmbulance(
        total=amb_counts["total"],
        statusCounts={
            "active": amb_counts["active"],
            "under_maintenance": amb_counts["under_maintenance"],
            "out_of_service": amb_counts["out_of_service"]
        },
        ownershipCounts={
            "private": amb_counts["private_count"],
            "public": amb_counts["public_count"]
        }
    )
    
    # Health facility overview card
    # Get facility counts
    stmt_fac = select(PartnerFacility.ownership_type, PartnerFacility.facility_location, func.count(PartnerFacility.id))
    stmt_fac = stmt_fac.where(PartnerFacility.added_by_id == current_user.id).group_by(
        PartnerFacility.ownership_type, PartnerFacility.facility_location
    )
    res_fac = await db.execute(stmt_fac)
    fac_rows = res_fac.all()
    
    fac_total = sum(r[2] for r in fac_rows)
    fac_pub = sum(r[2] for r in fac_rows if r[0] and r[0].lower() == "public")
    fac_priv = sum(r[2] for r in fac_rows if r[0] and r[0].lower() == "private")
    fac_urb = sum(r[2] for r in fac_rows if r[1] and r[1].lower() == "urban")
    fac_rur = sum(r[2] for r in fac_rows if r[1] and r[1].lower() == "rural")
    
    card_fac = OverviewCardHealthFacility(
        total=fac_total,
        ownershipType={
            "public": fac_pub,
            "private": fac_priv
        },
        facilityLocation={
            "urban": fac_urb,
            "rural": fac_rur
        }
    )
    
    # Required & Gaps overview cards (8901 required is default based on Connect frontend mocks)
    req_count = 8901
    active_amb = amb_counts["active"]
    gap_count = max(0, req_count - active_amb)
    cov_pct = round(active_amb / req_count, 4) if req_count > 0 else 0.0
    gap_pct = round(gap_count / req_count, 4) if req_count > 0 else 0.0
    
    card_req = OverviewCardRequired(
        requiredAmbulances=req_count,
        coveragePercentage=cov_pct,
        gapPercentage=gap_pct
    )
    
    card_gaps = OverviewCardGaps(
        gapCount=gap_count,
        coveragePercentage=cov_pct,
        gapPercentage=gap_pct
    )
    
    overview_cards = OverviewCardsContainer(
        ambulance=card_amb,
        healthFacility=card_fac,
        required=card_req,
        gaps=card_gaps
    )
    
    return {
        "success": True,
        "message": "Fetched successfully",
        "data": DashboardOverviewContainer(
            overViewList=overview_list,
            overViewCards=overview_cards
        )
    }

# --- Ambulances ---
@router.get("/ambulances", response_model=PartnerAmbulancesListResponse)
async def get_ambulances(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 10,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Get detailed partner ambulances list and summaries."""
    skip = (page - 1) * pageSize
    ambulances, total = await crud_partner_ambulance.get_multi_with_count(
        db, skip=skip, limit=pageSize, added_by_id=current_user.id
    )
    
    data_list = []
    for amb in ambulances:
        basic_info = AmbBasicInformation(
            plateNumber=amb.plate_number,
            make=amb.make,
            model=amb.model,
            year=amb.year,
            accreditationType=amb.accreditation_type,
            state=map_id_name(amb.state),
            lga=map_id_name(amb.lga),
            ward=map_id_name(amb.ward),
            facility=map_id_name(amb.facility),
            vehicleOwnershipType=amb.vehicle_ownership_type,
            driverName=amb.driver_name,
            contactNumber=amb.contact_number,
            createdAt=amb.created_at.date().isoformat() if amb.created_at else "",
            updatedAt=amb.updated_at.date().isoformat() if amb.updated_at else ""
        )
        
        tech_spec = AmbTechnicalSpecification(
            fuelType=amb.fuel_type,
            otherFuelTypeOption=amb.other_fuel_type_option or "",
            fuelCapicity=amb.fuel_capacity,
            communicationDevices=amb.communication_devices.split(",") if amb.communication_devices else [],
            otherCommunicationDeviceOption=amb.other_communication_device_option or "",
            latitude=amb.latitude,
            longitude=amb.longitude
        )
        
        equip_inv = AmbEquipmentInventory(
            equipments=amb.equipments.split(",") if amb.equipments else []
        )
        
        compliance = AmbComplianceAndDocumentation(
            roadWorthinessAssessmentDate=amb.road_worthiness_assessment_date.date().isoformat() if amb.road_worthiness_assessment_date else None,
            roadWorthinessStatus=amb.road_worthiness_status,
            lastInspectionDate=amb.last_inspection_date.date().isoformat() if amb.last_inspection_date else None,
            nextScheduledMaintenance=amb.next_scheduled_maintenance.date().isoformat() if amb.next_scheduled_maintenance else None,
            inspectionNotes=amb.inspection_notes,
            insuranceProvider=amb.insurance_provider,
            insuranceExpirationDate=amb.insurance_expiration_date.date().isoformat() if amb.insurance_expiration_date else None
        )
        
        status_info = AmbStatus(
            status=amb.status,
            isOutForMaintenance=amb.is_out_for_maintenance,
            isOutOfService=amb.is_out_of_service
        )
        
        data_list.append(PartnerAmbulanceResponse(
            id=amb.id,
            ambulanceId=amb.ambulance_id_str,
            basicInformation=basic_info,
            technicalSpecification=tech_spec,
            equipmentInventory=equip_inv,
            complianceAndDocumentation=compliance,
            documents={},
            status=status_info
        ))
        
    pagination = PaginationSchema(
        total=total,
        page=page,
        limit=pageSize
    )
    
    amb_counts = await crud_partner_ambulance.get_summary_counts(db, added_by_id=current_user.id)
    summary = AmbulanceListSummary(
        total=amb_counts["total"],
        active=amb_counts["active"],
        outOfService=amb_counts["out_of_service"],
        outForMaintenance=amb_counts["under_maintenance"]
    )
    
    return {
        "success": True,
        "message": "Fetched successfully",
        "data": AmbulancesListContainer(
            ambulances=AmbulancesContainer(
                data=data_list,
                pagination=pagination
            ),
            ambulanceSummary=summary
        )
    }

@router.post("/ambulances", response_model=PartnerAmbulanceResponse)
async def create_ambulance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    amb_in: PartnerAmbulanceCreate,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Create a new partner ambulance."""
    amb = await crud_partner_ambulance.create(db, obj_in=amb_in, added_by_id=current_user.id)
    
    basic_info = AmbBasicInformation(
        plateNumber=amb.plate_number,
        make=amb.make,
        model=amb.model,
        year=amb.year,
        accreditationType=amb.accreditation_type,
        state=map_id_name(amb.state),
        lga=map_id_name(amb.lga),
        ward=map_id_name(amb.ward),
        facility=map_id_name(amb.facility),
        vehicleOwnershipType=amb.vehicle_ownership_type,
        driverName=amb.driver_name,
        contactNumber=amb.contact_number,
        createdAt=amb.created_at.date().isoformat() if amb.created_at else "",
        updatedAt=amb.updated_at.date().isoformat() if amb.updated_at else ""
    )
    tech_spec = AmbTechnicalSpecification(
        fuelType=amb.fuel_type,
        fuelCapicity=amb.fuel_capacity,
        communicationDevices=amb.communication_devices.split(",") if amb.communication_devices else [],
        latitude=amb.latitude,
        longitude=amb.longitude
    )
    equip_inv = AmbEquipmentInventory(
        equipments=amb.equipments.split(",") if amb.equipments else []
    )
    compliance = AmbComplianceAndDocumentation(
        roadWorthinessAssessmentDate=amb.road_worthiness_assessment_date.date().isoformat() if amb.road_worthiness_assessment_date else None,
        roadWorthinessStatus=amb.road_worthiness_status,
        lastInspectionDate=amb.last_inspection_date.date().isoformat() if amb.last_inspection_date else None,
        nextScheduledMaintenance=amb.next_scheduled_maintenance.date().isoformat() if amb.next_scheduled_maintenance else None,
        inspectionNotes=amb.inspection_notes,
        insuranceProvider=amb.insurance_provider,
        insuranceExpirationDate=amb.insurance_expiration_date.date().isoformat() if amb.insurance_expiration_date else None
    )
    status_info = AmbStatus(
        status=amb.status,
        isOutForMaintenance=amb.is_out_for_maintenance,
        isOutOfService=amb.is_out_of_service
    )
    
    return PartnerAmbulanceResponse(
        id=amb.id,
        ambulanceId=amb.ambulance_id_str,
        basicInformation=basic_info,
        technicalSpecification=tech_spec,
        equipmentInventory=equip_inv,
        complianceAndDocumentation=compliance,
        status=status_info
    )

# --- Facilities ---
@router.get("/facilities", response_model=PartnerFacilitiesListResponse)
async def get_facilities(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 10,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Get list of partner health facilities."""
    skip = (page - 1) * pageSize
    facilities, total = await crud_partner_facility.get_multi_with_count(
        db, skip=skip, limit=pageSize, added_by_id=current_user.id
    )
    
    data_list = []
    for fac in facilities:
        data_list.append(PartnerFacilityResponse(
            id=fac.id,
            facilityId=fac.facility_id_str,
            facilityName=fac.facility_name,
            facilityType=fac.facility_type,
            facilityLocation=fac.facility_location,
            ownershipType=fac.ownership_type,
            communicationDevices=fac.communication_devices.split(",") if fac.communication_devices else [],
            numberOfAmbulance=fac.number_of_ambulance,
            facilityAddress=fac.address,
            facilityContactInformation=fac.contact_information,
            state=map_id_name(fac.state),
            lga=map_id_name(fac.lga),
            ward=map_id_name(fac.ward),
            status=fac.status,
            dateAdded=fac.date_added.date().isoformat() if fac.date_added else "",
            addedBy=map_added_by(fac.added_by) if fac.added_by else AddedBySchema(id=0, first_name="", last_name="")
        ))
        
    pagination = PaginationSchema(
        total=total,
        page=page,
        limit=pageSize
    )
    
    return {
        "success": True,
        "message": "Fetched successfully",
        "data": FacilitiesContainer(
            data=data_list,
            pagination=pagination
        )
    }

@router.post("/facilities", response_model=PartnerFacilityResponse)
async def create_facility(
    *,
    db: AsyncSession = Depends(deps.get_db),
    facility_in: PartnerFacilityCreate,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Create a new facility request."""
    fac = await crud_partner_facility.create(db, obj_in=facility_in, added_by_id=current_user.id)
    return PartnerFacilityResponse(
        id=fac.id,
        facilityId=fac.facility_id_str,
        facilityName=fac.facility_name,
        facilityType=fac.facility_type,
        facilityLocation=fac.facility_location,
        ownershipType=fac.ownership_type,
        communicationDevices=fac.communication_devices.split(",") if fac.communication_devices else [],
        numberOfAmbulance=fac.number_of_ambulance,
        facilityAddress=fac.address,
        facilityContactInformation=fac.contact_information,
        state=map_id_name(fac.state),
        lga=map_id_name(fac.lga),
        ward=map_id_name(fac.ward),
        status=fac.status,
        dateAdded=fac.date_added.date().isoformat() if fac.date_added else "",
        addedBy=map_added_by(fac.added_by) if fac.added_by else AddedBySchema(id=0, first_name="", last_name="")
    )

# --- Pledges ---
@router.get("/pledges", response_model=PartnerPledgesListResponse)
async def get_pledges(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 10,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Get partner pledges list and overview summaries."""
    skip = (page - 1) * pageSize
    pledges, total = await crud_partner_pledge.get_multi_with_count(
        db, skip=skip, limit=pageSize, added_by_id=None
    )
    
    data_list = []
    for plg in pledges:
        data_list.append(PartnerPledgeResponse(
            id=plg.id,
            pledgeId=plg.pledge_id_str,
            contactDetails=plg.contact_details,
            donorName=plg.donor_name,
            pledgeType=plg.pledge_type,
            numberOfAmbulance=plg.number_of_ambulance,
            ambulanceType=map_id_name(plg.ambulance_type),
            ward=map_id_name(plg.ward),
            state=map_id_name(plg.state),
            lga=map_id_name(plg.lga),
            facility=map_id_name(plg.facility),
            pledgeDate=plg.pledge_date.date().isoformat() if plg.pledge_date else None,
            deliveryDate=plg.delivery_date.date().isoformat() if plg.delivery_date else None,
            status=plg.status,
            dateAdded=plg.date_added.date().isoformat() if plg.date_added else "",
            addedBy=map_added_by(plg.added_by) if plg.added_by else AddedBySchema(id=0, first_name="", last_name="")
        ))
        
    counts = await crud_partner_pledge.get_summary(db, added_by_id=None)
    summary = PledgeSummary(
        total=counts["total"],
        pending=counts["pending"],
        fulfilled=counts["fulfilled"],
        notFulfilled=counts["notFulfilled"]
    )
    
    return {
        "success": True,
        "message": "Fetched successfully",
        "data": PledgesListContainer(
            summary=summary,
            list=PledgesListData(data=data_list)
        )
    }

@router.post("/pledges", response_model=PartnerPledgeResponse)
async def create_pledge(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pledge_in: PartnerPledgeCreate,
    current_user: PartnerUser = Depends(deps.get_current_partner_user)
) -> Any:
    """Create a new pledge."""
    plg = await crud_partner_pledge.create(db, obj_in=pledge_in, added_by_id=current_user.id)
    return PartnerPledgeResponse(
        id=plg.id,
        pledgeId=plg.pledge_id_str,
        contactDetails=plg.contact_details,
        donorName=plg.donor_name,
        pledgeType=plg.pledge_type,
        numberOfAmbulance=plg.number_of_ambulance,
        ambulanceType=map_id_name(plg.ambulance_type),
        ward=map_id_name(plg.ward),
        state=map_id_name(plg.state),
        lga=map_id_name(plg.lga),
        facility=map_id_name(plg.facility),
        pledgeDate=plg.pledge_date.date().isoformat() if plg.pledge_date else None,
        deliveryDate=plg.delivery_date.date().isoformat() if plg.delivery_date else None,
        status=plg.status,
        dateAdded=plg.date_added.date().isoformat() if plg.date_added else "",
        addedBy=map_added_by(plg.added_by) if plg.added_by else AddedBySchema(id=0, first_name="", last_name="")
    )
