from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.ambulance import Ambulance, GPSHistory, AmbulanceStatus, Dispatch, IncidentLeg
from src.schemas.ambulance import AmbulanceCreate, AmbulanceUpdate, GPSHistoryCreate
from typing import List, Optional, Any
import math
from datetime import datetime, timezone

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
    def _calculate_distance(lat1, lon1, lat2, lon2):
        """Haversine formula to calculate distance between two points in km."""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    async def update_gps(
        db: AsyncSession, ambulance_id: int, obj_in: GPSHistoryCreate, state_id: Optional[int] = None
    ) -> Ambulance:
        ambulance = await AmbulanceService.get_by_id(db, ambulance_id=ambulance_id, state_id=state_id)
        if not ambulance:
            return None
        
        # Calculate distance delta since last update
        delta = 0.0
        if ambulance.last_latitude and ambulance.last_longitude:
            delta = AmbulanceService._calculate_distance(
                ambulance.last_latitude, ambulance.last_longitude,
                obj_in.latitude, obj_in.longitude
            )
        
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
            incident_leg=obj_in.incident_leg,
            delta_distance=delta
        )
        db.add(history)
        
        # Update total distance for the active dispatch if applicable
        if obj_in.incident_id:
            # Find active dispatch for this incident and ambulance
            stmt = select(Dispatch).where(
                Dispatch.incident_id == obj_in.incident_id,
                Dispatch.ambulance_id == ambulance_id,
                Dispatch.completed_timestamp == None
            )
            result = await db.execute(stmt)
            dispatch = result.scalars().first()
            if dispatch:
                dispatch.total_distance += delta

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
