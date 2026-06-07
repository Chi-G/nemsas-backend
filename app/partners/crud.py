from typing import List, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import selectinload
from app.partners.models import PartnerUser, PartnerPledge, PartnerFacility, PartnerAmbulance
from app.partners.schemas import PartnerRegister, PartnerPledgeCreate, PartnerFacilityCreate, PartnerAmbulanceCreate
from app.core.security import get_password_hash

class CRUDPartnerUser:
    async def get(self, db: AsyncSession, id: int) -> Optional[PartnerUser]:
        result = await db.execute(select(PartnerUser).where(PartnerUser.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[PartnerUser]:
        result = await db.execute(select(PartnerUser).where(func.lower(PartnerUser.email) == func.lower(email)))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: PartnerRegister) -> PartnerUser:
        # Determine userType: if organisation_name is present, it's 'organization', otherwise 'partner'
        user_type = obj_in.user_type
        if not user_type or not user_type.strip():
            if obj_in.organisation_name and obj_in.organisation_name.strip():
                user_type = "organization"
            else:
                user_type = "partner"

        db_obj = PartnerUser(
            first_name=obj_in.first_name,
            middle_name=obj_in.middle_name,
            last_name=obj_in.last_name,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            phone_number=obj_in.phone_number,
            organisation_name=obj_in.organisation_name,
            user_type=user_type
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

class CRUDPartnerPledge:
    def _get_pledge_options(self) -> List[Any]:
        return [
            selectinload(PartnerPledge.added_by),
            selectinload(PartnerPledge.ambulance_type),
            selectinload(PartnerPledge.state),
            selectinload(PartnerPledge.lga),
            selectinload(PartnerPledge.ward),
            selectinload(PartnerPledge.facility)
        ]

    async def get_multi_with_count(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, added_by_id: Optional[int] = None
    ) -> Tuple[List[PartnerPledge], int]:
        stmt = select(PartnerPledge).options(*self._get_pledge_options()).order_by(desc(PartnerPledge.id))
        count_stmt = select(func.count(PartnerPledge.id))
        
        if added_by_id is not None:
            stmt = stmt.where(PartnerPledge.added_by_id == added_by_id)
            count_stmt = count_stmt.where(PartnerPledge.added_by_id == added_by_id)
            
        total = await db.scalar(count_stmt) or 0
        res = await db.execute(stmt.offset(skip).limit(limit))
        return list(res.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: PartnerPledgeCreate, added_by_id: int) -> PartnerPledge:
        # Determine next ID for unique string prefix
        max_id_stmt = select(func.max(PartnerPledge.id))
        max_id = await db.scalar(max_id_stmt) or 0
        next_id = max_id + 1
        
        pledge_id_str = f"PLG-{next_id:05d}"
        
        db_obj = PartnerPledge(
            pledge_id_str=pledge_id_str,
            contact_details=obj_in.contact_details,
            donor_name=obj_in.donor_name,
            pledge_type=obj_in.pledge_type,
            number_of_ambulance=obj_in.number_of_ambulance,
            ambulance_type_id=obj_in.ambulance_type_id,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            ward_id=obj_in.ward_id,
            facility_id=obj_in.facility_id,
            pledge_date=obj_in.pledge_date,
            delivery_date=obj_in.delivery_date,
            status=obj_in.status or "pending",
            added_by_id=added_by_id
        )
        db.add(db_obj)
        await db.commit()
        
        # Fresh eager load
        db.expunge(db_obj)
        stmt = select(PartnerPledge).options(*self._get_pledge_options()).where(PartnerPledge.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_summary(self, db: AsyncSession, added_by_id: Optional[int] = None) -> dict:
        stmt = select(PartnerPledge.status, func.count(PartnerPledge.id))
        if added_by_id is not None:
            stmt = stmt.where(PartnerPledge.added_by_id == added_by_id)
        stmt = stmt.group_by(PartnerPledge.status)
        
        res = await db.execute(stmt)
        rows = res.all()
        
        counts = {row[0].lower() if row[0] else "pending": row[1] for row in rows}
        total = sum(counts.values())
        
        return {
            "total": total,
            "pending": counts.get("pending", 0),
            "fulfilled": counts.get("fulfilled", 0),
            "notFulfilled": counts.get("not_fulfilled", 0) + counts.get("notfulfilled", 0)
        }

class CRUDPartnerFacility:
    def _get_facility_options(self) -> List[Any]:
        return [
            selectinload(PartnerFacility.added_by),
            selectinload(PartnerFacility.state),
            selectinload(PartnerFacility.lga),
            selectinload(PartnerFacility.ward)
        ]

    async def get_multi_with_count(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, added_by_id: Optional[int] = None
    ) -> Tuple[List[PartnerFacility], int]:
        stmt = select(PartnerFacility).options(*self._get_facility_options()).order_by(desc(PartnerFacility.id))
        count_stmt = select(func.count(PartnerFacility.id))
        
        if added_by_id is not None:
            stmt = stmt.where(PartnerFacility.added_by_id == added_by_id)
            count_stmt = count_stmt.where(PartnerFacility.added_by_id == added_by_id)
            
        total = await db.scalar(count_stmt) or 0
        res = await db.execute(stmt.offset(skip).limit(limit))
        return list(res.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: PartnerFacilityCreate, added_by_id: int) -> PartnerFacility:
        max_id_stmt = select(func.max(PartnerFacility.id))
        max_id = await db.scalar(max_id_stmt) or 0
        next_id = max_id + 1
        
        facility_id_str = f"Fac-{next_id:05d}"
        
        devices_str = ",".join(obj_in.communication_devices) if obj_in.communication_devices else ""
        
        db_obj = PartnerFacility(
            facility_id_str=facility_id_str,
            facility_name=obj_in.facility_name,
            facility_type=obj_in.facility_type,
            facility_location=obj_in.facility_location,
            ownership_type=obj_in.ownership_type,
            communication_devices=devices_str,
            number_of_ambulance=obj_in.number_of_ambulance,
            address=obj_in.address,
            contact_information=obj_in.contact_information,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            ward_id=obj_in.ward_id,
            status="approved", # Defaulting approved for demo/flow convenience, or pending
            added_by_id=added_by_id
        )
        db.add(db_obj)
        await db.commit()
        
        db.expunge(db_obj)
        stmt = select(PartnerFacility).options(*self._get_facility_options()).where(PartnerFacility.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

class CRUDPartnerAmbulance:
    def _get_ambulance_options(self) -> List[Any]:
        return [
            selectinload(PartnerAmbulance.added_by),
            selectinload(PartnerAmbulance.state),
            selectinload(PartnerAmbulance.lga),
            selectinload(PartnerAmbulance.ward),
            selectinload(PartnerAmbulance.facility)
        ]

    async def get_multi_with_count(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, added_by_id: Optional[int] = None
    ) -> Tuple[List[PartnerAmbulance], int]:
        stmt = select(PartnerAmbulance).options(*self._get_ambulance_options()).order_by(desc(PartnerAmbulance.id))
        count_stmt = select(func.count(PartnerAmbulance.id))
        
        if added_by_id is not None:
            stmt = stmt.where(PartnerAmbulance.added_by_id == added_by_id)
            count_stmt = count_stmt.where(PartnerAmbulance.added_by_id == added_by_id)
            
        total = await db.scalar(count_stmt) or 0
        res = await db.execute(stmt.offset(skip).limit(limit))
        return list(res.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: PartnerAmbulanceCreate, added_by_id: int) -> PartnerAmbulance:
        max_id_stmt = select(func.max(PartnerAmbulance.id))
        max_id = await db.scalar(max_id_stmt) or 0
        next_id = max_id + 1
        
        ambulance_id_str = f"Amb {next_id}"
        
        devices_str = ",".join(obj_in.communication_devices) if obj_in.communication_devices else ""
        equipments_str = ",".join(obj_in.equipments) if obj_in.equipments else ""
        
        db_obj = PartnerAmbulance(
            ambulance_id_str=ambulance_id_str,
            plate_number=obj_in.plate_number,
            make=obj_in.make,
            model=obj_in.model,
            year=obj_in.year,
            accreditation_type=obj_in.accreditation_type,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            ward_id=obj_in.ward_id,
            facility_id=obj_in.facility_id,
            vehicle_ownership_type=obj_in.vehicle_ownership_type,
            driver_name=obj_in.driver_name,
            contact_number=obj_in.contact_number,
            fuel_type=obj_in.fuel_type,
            other_fuel_type_option=obj_in.other_fuel_type_option or "",
            fuel_capacity=obj_in.fuel_capacity,
            communication_devices=devices_str,
            other_communication_device_option=obj_in.other_communication_device_option or "",
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            equipments=equipments_str,
            road_worthiness_assessment_date=obj_in.road_worthiness_assessment_date,
            road_worthiness_status=obj_in.road_worthiness_status or "passed",
            last_inspection_date=obj_in.last_inspection_date,
            next_scheduled_maintenance=obj_in.next_scheduled_maintenance,
            inspection_notes=obj_in.inspection_notes or "N/A",
            insurance_provider=obj_in.insurance_provider or "N/A",
            insurance_expiration_date=obj_in.insurance_expiration_date,
            status="active",
            added_by_id=added_by_id
        )
        db.add(db_obj)
        await db.commit()
        
        db.expunge(db_obj)
        stmt = select(PartnerAmbulance).options(*self._get_ambulance_options()).where(PartnerAmbulance.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_summary_counts(self, db: AsyncSession, added_by_id: Optional[int] = None) -> dict:
        # We need counts for total, active, out_of_service, and under_maintenance
        stmt_active = select(func.count(PartnerAmbulance.id)).where(
            PartnerAmbulance.status == "active",
            PartnerAmbulance.is_out_for_maintenance == False,
            PartnerAmbulance.is_out_of_service == False
        )
        stmt_maint = select(func.count(PartnerAmbulance.id)).where(PartnerAmbulance.is_out_for_maintenance == True)
        stmt_service = select(func.count(PartnerAmbulance.id)).where(PartnerAmbulance.is_out_of_service == True)
        stmt_total = select(func.count(PartnerAmbulance.id))
        
        if added_by_id is not None:
            stmt_active = stmt_active.where(PartnerAmbulance.added_by_id == added_by_id)
            stmt_maint = stmt_maint.where(PartnerAmbulance.added_by_id == added_by_id)
            stmt_service = stmt_service.where(PartnerAmbulance.added_by_id == added_by_id)
            stmt_total = stmt_total.where(PartnerAmbulance.added_by_id == added_by_id)
            
        total = await db.scalar(stmt_total) or 0
        active = await db.scalar(stmt_active) or 0
        maintenance = await db.scalar(stmt_maint) or 0
        out_of_service = await db.scalar(stmt_service) or 0
        
        # Ownership counts
        stmt_ownership = select(PartnerAmbulance.vehicle_ownership_type, func.count(PartnerAmbulance.id))
        if added_by_id is not None:
            stmt_ownership = stmt_ownership.where(PartnerAmbulance.added_by_id == added_by_id)
        stmt_ownership = stmt_ownership.group_by(PartnerAmbulance.vehicle_ownership_type)
        res_own = await db.execute(stmt_ownership)
        ownership_counts = {row[0].lower() if row[0] else "private": row[1] for row in res_own.all()}
        
        return {
            "total": total,
            "active": active,
            "under_maintenance": maintenance,
            "out_of_service": out_of_service,
            "private_count": ownership_counts.get("private", 0),
            "public_count": ownership_counts.get("public", 0)
        }

partner_user = CRUDPartnerUser()
partner_pledge = CRUDPartnerPledge()
partner_facility = CRUDPartnerFacility()
partner_ambulance = CRUDPartnerAmbulance()
