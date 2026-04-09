import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.incident import Incident, IncidentStatusHistory, IncidentStatus
from src.schemas.incident import IncidentCreate, IncidentUpdate
from typing import List, Optional, Any

class IncidentService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: IncidentCreate, creator_id: int) -> Incident:
        db_obj = Incident(
            uuid=str(uuid.uuid4()),
            location_label=obj_in.location_label,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            emergency_type=obj_in.emergency_type,
            severity=obj_in.severity,
            patient_count=obj_in.patient_count,
            notes=obj_in.notes,
            caller_name=obj_in.caller_name,
            caller_phone=obj_in.caller_phone,
            status=IncidentStatus.CREATED,
        )
        db.add(db_obj)
        await db.flush() # Get ID
        
        # Add initial status history
        history = IncidentStatusHistory(
            incident_id=db_obj.id,
            status=IncidentStatus.CREATED,
            changed_by_id=creator_id,
            notes="Initial creation",
        )
        db.add(history)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_by_uuid(db: AsyncSession, uuid_str: str, state_id: Optional[int] = None) -> Optional[Incident]:
        stmt = select(Incident).where(Incident.uuid == uuid_str)
        if state_id:
            stmt = stmt.where(Incident.state_id == state_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_uuid_or_id(
        db: AsyncSession, uuid_str: str = None, id: int = None, state_id: Optional[int] = None
    ) -> Optional[Incident]:
        if uuid_str:
            stmt = select(Incident).where(Incident.uuid == uuid_str)
        elif id:
            stmt = select(Incident).where(Incident.id == id)
        else:
            return None
            
        if state_id:
            stmt = stmt.where(Incident.state_id == state_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def update_status(
        db: AsyncSession, db_obj: Incident, new_status: IncidentStatus, changer_id: int, notes: str = None
    ) -> Incident:
        # Validate transition (simplified logic)
        db_obj.status = new_status
        history = IncidentStatusHistory(
            incident_id=db_obj.id,
            status=new_status,
            changed_by_id=changer_id,
            notes=notes,
        )
        db.add(history)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

incident_service = IncidentService()
