from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List, Optional, Tuple
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate

class CRUDIncident:
    async def get(self, db: AsyncSession, id: int) -> Optional[Incident]:
        result = await db.execute(select(Incident).filter(Incident.id == id))
        return result.scalars().first()

    async def get_multi_with_count(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        triage: Optional[str] = None,
        state: Optional[str] = None
    ) -> Tuple[List[Incident], int]:
        query = select(Incident)

        if search:
            search_filter = or_(
                Incident.serial_no.ilike(f"%{search}%"),
                Incident.caller_name.ilike(f"%{search}%"),
                Incident.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        if status:
            query = query.filter(Incident.incident_status_type == status)
        if triage:
            query = query.filter(Incident.triage_category == triage)
        if state:
            query = query.filter(Incident.state_name.ilike(f"%{state}%"))

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Records
        result = await db.execute(
            query.order_by(Incident.date_added.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: IncidentCreate) -> Incident:
        db_obj = Incident(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

incident_crud = CRUDIncident()
