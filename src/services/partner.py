from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.db.models.partner import Partner, Pledge, FacilityRequest, Facility, PledgeStatus, FacilityRequestStatus
from src.db.models.user import User
from src.db.models.auth import TokenType
from src.schemas.partner import (
    PartnerRegister, PartnerVerifyOTP, PledgeCreate, 
    PledgeStatusUpdate, FacilityRequestCreate, PartnerApproval, PartnerRejection
)
from src.services.auth import auth_service
from src.services.email import email_service
from src.services.reference import reference_service
from src.core.rbac import RoleName
from sqlalchemy.orm import selectinload
from typing import List, Optional, Any
from fastapi import HTTPException, status

class PartnerService:
    @staticmethod
    async def get_role_id_by_name(db: AsyncSession, name: str) -> int:
        from src.db.models.user import Role
        result = await db.execute(select(Role).where(Role.name == name))
        role = result.scalars().first()
        if not role:
            raise HTTPException(status_code=500, detail=f"Role {name} not found")
        return role.id

    @staticmethod
    async def register_partner(db: AsyncSession, obj_in: PartnerRegister) -> Partner:
        # 1. Check if user already exists
        result = await db.execute(select(User).where(User.email == obj_in.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # 2. Create User (Inactive)
        role_id = await PartnerService.get_role_id_by_name(db, RoleName.PARTNER)
        user = User(
            email=obj_in.email,
            name=obj_in.organisation_name,
            hashed_password="!!!UNACTIVATED_PARTNER_ACCOUNT!!!", # Placeholder until activation
            is_active=False,
            role_id=role_id
        )
        db.add(user)
        await db.flush()

        # 3. Create Partner Profile
        partner = Partner(
            user_id=user.id,
            organisation_name=obj_in.organisation_name,
            contact_person=obj_in.contact_person,
            contact_phone=obj_in.contact_phone,
            address=obj_in.address,
            is_verified=False
        )
        db.add(partner)
        await db.flush()

        # 4. Generate & Send OTP
        token = await auth_service.create_token(db, user_id=user.id, token_type=TokenType.TWO_FACTOR, expires_in_minutes=10)
        await email_service.send_partner_2fa(email=user.email, otp=token.token)
        
        await db.commit()
        await db.refresh(partner)
        return partner

    @staticmethod
    async def verify_partner_otp(db: AsyncSession, obj_in: PartnerVerifyOTP) -> Partner:
        # Use existing auth service to verify token
        user = await auth_service.verify_and_use_token(db, token_str=obj_in.otp, token_type=TokenType.TWO_FACTOR)
        if not user or user.email != obj_in.email:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        result = await db.execute(select(Partner).where(Partner.user_id == user.id))
        partner = result.scalars().first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner profile not found")

        partner.is_verified = True
        await db.commit()
        await db.refresh(partner)
        return partner

    @staticmethod
    async def approve_partner(db: AsyncSession, partner_id: int, admin_id: int) -> Partner:
        stmt = select(Partner).options(selectinload(Partner.user)).where(Partner.id == partner_id)
        result = await db.execute(stmt)
        partner = result.scalars().first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        if not partner.is_verified:
            raise HTTPException(status_code=400, detail="Partner must verify OTP before approval")

        partner.user.is_active = True
        
        # Log Audit
        from src.services.reference import reference_service
        await reference_service.log_audit(db, admin_id, "partners", partner_id, "APPROVE", {"status": "Active"})
        
        # Trigger activation link/email (already exists in email service)
        token = await auth_service.create_token(db, user_id=partner.user.id, token_type=TokenType.RESET, expires_in_minutes=24*60)
        await email_service.send_account_activation(email=partner.user.email, token=token.token)
        
        await db.commit()
        await db.refresh(partner)
        return partner

    @staticmethod
    async def create_pledge(db: AsyncSession, partner_id: int, obj_in: PledgeCreate) -> Pledge:
        pledge = Pledge(
            partner_id=partner_id,
            **obj_in.model_dump(),
            status=PledgeStatus.PENDING,
            fulfilled_count=0
        )
        db.add(pledge)
        await db.commit()
        await db.refresh(pledge)
        return pledge

    @staticmethod
    async def create_facility_request(db: AsyncSession, partner_id: int, obj_in: FacilityRequestCreate) -> FacilityRequest:
        req = FacilityRequest(
            partner_id=partner_id,
            **obj_in.model_dump(),
            status=FacilityRequestStatus.PENDING
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def approve_facility_request(db: AsyncSession, request_id: int, admin_id: int) -> Facility:
        stmt = select(FacilityRequest).where(FacilityRequest.id == request_id)
        result = await db.execute(stmt)
        req = result.scalars().first()
        if not req:
            raise HTTPException(status_code=404, detail="Facility request not found")
        
        if req.status == FacilityRequestStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Request already approved")

        # Create facility in registry
        facility = Facility(
            name=req.facility_name,
            facility_type=req.facility_type,
            address=req.address,
            latitude=req.latitude,
            longitude=req.longitude,
            state_id=req.state_id,
            lga_id=req.lga_id,
            is_active=True
        )
        db.add(facility)
        req.status = FacilityRequestStatus.APPROVED
        
        await reference_service.log_audit(db, admin_id, "facility_requests", request_id, "APPROVE", {"facility_id": facility.id})
        await db.commit()
        await db.refresh(facility)
        return facility

    @staticmethod
    async def get_pledges(
        db: AsyncSession, 
        partner_id: Optional[int] = None, 
        status: Optional[PledgeStatus] = None,
        state_id: Optional[int] = None
    ) -> List[Pledge]:
        stmt = select(Pledge)
        if partner_id:
            stmt = stmt.where(Pledge.partner_id == partner_id)
        if status:
            stmt = stmt.where(Pledge.status == status)
        if state_id:
            stmt = stmt.where(Pledge.target_state_id == state_id)
        
        result = await db.execute(stmt.order_by(Pledge.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def update_pledge_status(db: AsyncSession, pledge_id: int, status_in: PledgeStatus, admin_id: int) -> Pledge:
        stmt = select(Pledge).where(Pledge.id == pledge_id)
        result = await db.execute(stmt)
        pledge = result.scalars().first()
        if not pledge:
            raise HTTPException(status_code=404, detail="Pledge not found")
            
        old_status = pledge.status
        pledge.status = status_in
        
        await reference_service.log_audit(db, admin_id, "pledges", pledge_id, "UPDATE_STATUS", {"old": old_status, "new": status_in})
        await db.commit()
        await db.refresh(pledge)
        return pledge

    @staticmethod
    async def get_facility_requests(
        db: AsyncSession, 
        partner_id: Optional[int] = None,
        status: Optional[FacilityRequestStatus] = None
    ) -> List[FacilityRequest]:
        stmt = select(FacilityRequest)
        if partner_id:
            stmt = stmt.where(FacilityRequest.partner_id == partner_id)
        if status:
            stmt = stmt.where(FacilityRequest.status == status)
            
        result = await db.execute(stmt.order_by(FacilityRequest.created_at.desc()))
        return result.scalars().all()

partner_service = PartnerService()
