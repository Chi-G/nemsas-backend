from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate

class CRUDIncident:
    async def get(self, db: AsyncSession, id: int) -> Optional[Incident]:
        stmt = select(Incident).options(selectinload(Incident.patients)).where(Incident.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        state_id: Optional[int] = None
    ) -> Tuple[List[Incident], int]:
        stmt = select(Incident).options(selectinload(Incident.patients)).order_by(desc(Incident.id))
        
        # Basic query counting
        count_stmt = select(func.count()).select_from(Incident)
        
        # Can extend filters later as needed here
        
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

    async def create(self, db: AsyncSession, *, obj_in: IncidentCreate) -> Incident:
        db_obj = Incident(**obj_in.model_dump(exclude_unset=True))
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

incident = CRUDIncident()
