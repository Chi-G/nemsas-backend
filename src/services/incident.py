import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from src.db.models.incident import Incident, IncidentStatusHistory, IncidentStatus
from src.db.models.partner import Facility
from src.db.models.reference import LGA, State
from src.schemas.incident import IncidentCreate, IncidentUpdate
from src.core.constants import INCIDENT_TRANSITION_MAP
from typing import List, Optional, Any
from datetime import datetime

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
    async def list(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[IncidentStatus] = None,
        state_id: Optional[int] = None,
        lga_id: Optional[int] = None,
        emergency_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Incident]:
        query = select(Incident)
        
        if status:
            query = query.where(Incident.status == status)
        if state_id:
            query = query.where(Incident.state_id == state_id)
        if lga_id:
            query = query.where(Incident.lga_id == lga_id)
        if emergency_type:
            query = query.where(Incident.emergency_type == emergency_type)
        if start_date:
            query = query.where(Incident.created_at >= start_date)
        if end_date:
            query = query.where(Incident.created_at <= end_date)
            
        result = await db.execute(query.order_by(Incident.created_at.desc()).offset(skip).limit(limit))
        return result.scalars().all()

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
        # Criterion 63: Strict transition validation
        allowed_next_statuses = INCIDENT_TRANSITION_MAP.get(db_obj.status, [])
        if new_status not in allowed_next_statuses:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422, 
                detail=f"Invalid status transition from {db_obj.status} to {new_status}. Allowed: {[s.value for s in allowed_next_statuses]}"
            )

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

    @staticmethod
    async def search_locations(db: AsyncSession, query: str) -> List[dict]:
        """
        Criterion 62: Location search logic.
        Queries health facilities and LGAs for name matches.
        """
        results = []
        
        # Search Facilities
        facility_stmt = select(Facility).where(Facility.name.ilike(f"%{query}%")).limit(10)
        facility_res = await db.execute(facility_stmt)
        for f in facility_res.scalars().all():
            results.append({
                "label": f.name,
                "type": "Health Facility",
                "latitude": f.latitude,
                "longitude": f.longitude,
                "state_id": f.state_id,
                "lga_id": f.lga_id
            })
            
        # Search LGAs
        lga_stmt = select(LGA).where(LGA.name.ilike(f"%{query}%")).limit(10)
        lga_res = await db.execute(lga_stmt)
        for lga in lga_res.scalars().all():
            results.append({
                "label": f"LGA: {lga.name}",
                "type": "LGA",
                "latitude": 0.0, # Center of LGA (placeholder if not available)
                "longitude": 0.0,
                "state_id": lga.state_id,
                "lga_id": lga.id
            })
            
        return results

    @staticmethod
    async def get_full_incident(db: AsyncSession, uuid_str: str, state_id: Optional[int] = None) -> Optional[Incident]:
        """
        Criterion 66: Return full incident record with status history.
        """
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Incident)
            .where(Incident.uuid == uuid_str)
            .options(selectinload(Incident.status_history))
        )
        if state_id:
            stmt = stmt.where(Incident.state_id == state_id)
        result = await db.execute(stmt)
        return result.scalars().first()

incident_service = IncidentService()
