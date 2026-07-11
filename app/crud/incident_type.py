from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Tuple
from app.models.incident_type import IncidentType
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeUpdate

class CRUDIncidentType:
    async def get(self, db: AsyncSession, id: int) -> Optional[IncidentType]:
        result = await db.execute(select(IncidentType).filter(IncidentType.id == id))
        return result.scalars().first()

    async def get_multi_with_count(self, db: AsyncSession, status: Optional[str] = None) -> Tuple[List[IncidentType], int]:
        from sqlalchemy import func
        
        count_stmt = select(func.count()).select_from(IncidentType)
        query_stmt = select(IncidentType)
        
        if status != "all":
            count_stmt = count_stmt.where(IncidentType.is_active == True)
            query_stmt = query_stmt.where(IncidentType.is_active == True)
            
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        result = await db.execute(
            query_stmt.order_by(IncidentType.id.desc())
        )
        return list(result.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: IncidentTypeCreate) -> IncidentType:
        from sqlalchemy import func
        from datetime import datetime, timezone
        
        # Calculate next ID
        max_id = await db.scalar(select(func.max(IncidentType.id))) or 0
        
        db_obj = IncidentType(**obj_in.model_dump())
        db_obj.id = max_id + 1
        db_obj.date_added = datetime.now(timezone.utc)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def update(self, db: AsyncSession, *, db_obj: IncidentType, obj_in: IncidentTypeUpdate) -> IncidentType:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

incident_type_crud = CRUDIncidentType()
