from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.partner import Partner, Pledge, Facility, FacilityRequest, PledgeStatus, FacilityRequestStatus
from src.schemas.partner import PartnerCreate, PledgeCreate, FacilityRequestCreate
from datetime import datetime, timezone
from typing import List, Optional, Any

class PartnerService:
    @staticmethod
    async def create_partner(
        db: AsyncSession, obj_in: PartnerCreate
    ) -> Partner:
        db_obj = Partner(
            user_id=obj_in.user_id,
            organisation_name=obj_in.organisation_name,
            contact_person=obj_in.contact_person,
            contact_phone=obj_in.contact_phone,
            address=obj_in.address,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_partner_by_user_id(db: AsyncSession, user_id: int) -> Optional[Partner]:
        result = await db.execute(select(Partner).where(Partner.user_id == user_id))
        return result.scalars().first()

    @staticmethod
    async def create_pledge(
        db: AsyncSession, obj_in: PledgeCreate
    ) -> Pledge:
        db_obj = Pledge(
            partner_id=obj_in.partner_id,
            ambulance_count=obj_in.ambulance_count,
            target_state_id=obj_in.target_state_id,
            target_lga_id=obj_in.target_lga_id,
            status=PledgeStatus.PENDING,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def create_facility_request(
        db: AsyncSession, obj_in: FacilityRequestCreate
    ) -> FacilityRequest:
        db_obj = FacilityRequest(
            partner_id=obj_in.partner_id,
            facility_name=obj_in.facility_name,
            facility_type=obj_in.facility_type,
            address=obj_in.address,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            status=FacilityRequestStatus.PENDING,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def approve_facility_request(
        db: AsyncSession, request_id: int
    ) -> Optional[Facility]:
        result = await db.execute(select(FacilityRequest).where(FacilityRequest.id == request_id))
        req = result.scalars().first()
        if not req:
            return None
            
        req.status = FacilityRequestStatus.APPROVED
        
        # Add to the national registry
        facility = Facility(
            name=req.facility_name,
            facility_type=req.facility_type,
            address=req.address,
            latitude=req.latitude,
            longitude=req.longitude,
            state_id=req.state_id,
            lga_id=req.lga_id,
        )
        db.add(facility)
        await db.commit()
        await db.refresh(facility)
        return facility

partner_service = PartnerService()
