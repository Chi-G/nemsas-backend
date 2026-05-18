from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Tuple
from app.models.incident_type import IncidentType
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeUpdate

class CRUDIncidentType:
    async def get(self, db: AsyncSession, id: int) -> Optional[IncidentType]:
        result = await db.execute(select(IncidentType).filter(IncidentType.id == id))
        return result.scalars().first()

    async def get_multi_with_count(self, db: AsyncSession) -> Tuple[List[IncidentType], int]:
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(IncidentType)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        result = await db.execute(
            select(IncidentType)
            .order_by(IncidentType.id.desc())
        )
        return list(result.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: IncidentTypeCreate) -> IncidentType:
        db_obj = IncidentType(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

incident_type_crud = CRUDIncidentType()
