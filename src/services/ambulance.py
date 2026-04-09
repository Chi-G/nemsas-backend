from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.ambulance import Ambulance, GPSHistory, AmbulanceStatus
from src.schemas.ambulance import AmbulanceCreate, AmbulanceUpdate, GPSHistoryCreate
from typing import List, Optional, Any

class AmbulanceService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: AmbulanceCreate) -> Ambulance:
        db_obj = Ambulance(
            plate_number=obj_in.plate_number,
            make_model=obj_in.make_model,
            year=obj_in.year,
            accreditation_type=obj_in.accreditation_type,
            fuel_type=obj_in.fuel_type,
            capacity=obj_in.capacity,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            partner_id=obj_in.partner_id,
            status=AmbulanceStatus.ACTIVE,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, ambulance_id: int, state_id: Optional[int] = None) -> Optional[Ambulance]:
        stmt = select(Ambulance).where(Ambulance.id == ambulance_id)
        if state_id:
            stmt = stmt.where(Ambulance.state_id == state_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def update_gps(
        db: AsyncSession, ambulance_id: int, obj_in: GPSHistoryCreate, state_id: Optional[int] = None
    ) -> Ambulance:
        ambulance = await AmbulanceService.get_by_id(db, ambulance_id=ambulance_id, state_id=state_id)
        if not ambulance:
            return None
        
        # Update last known position
        ambulance.last_latitude = obj_in.latitude
        ambulance.last_longitude = obj_in.longitude
        
        # Store in history
        history = GPSHistory(
            ambulance_id=ambulance_id,
            incident_id=obj_in.incident_id,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            is_paused=obj_in.is_paused,
        )
        db.add(history)
        await db.commit()
        await db.refresh(ambulance)
        return ambulance

    @staticmethod
    async def update_status(
        db: AsyncSession, db_obj: Ambulance, new_status: AmbulanceStatus
    ) -> Ambulance:
        db_obj.status = new_status
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

ambulance_service = AmbulanceService()
