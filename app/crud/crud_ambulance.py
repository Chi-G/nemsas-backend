from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Any, Tuple
from app.models.ambulance import Ambulance



class CRUDAmbulance:
    async def get(self, db: AsyncSession, id: Any) -> Optional[Ambulance]:
        result = await db.execute(
            select(Ambulance)
            .filter(Ambulance.id == id)
            .options(
                selectinload(Ambulance.state),
                selectinload(Ambulance.lga),
                selectinload(Ambulance.ambulance_type)
            )
        )
        obj = result.scalars().first()
        if obj:
            await self._augment_busy_status(db, [obj])
        return obj

    async def _augment_busy_status(self, db: AsyncSession, ambulances: List[Ambulance]) -> None:
        if not ambulances:
            return
        amb_ids = [amb.id for amb in ambulances]
        from app.models.incident import Incident
        result = await db.execute(
            select(Incident.ambulance_id)
            .filter(Incident.ambulance_id.in_(amb_ids))
            .filter(Incident.event_status_type == "Patient Picked Up")
        )
        busy_amb_ids = set(result.scalars().all())
        for amb in ambulances:
            if amb.id in busy_amb_ids:
                amb.event_status_type = "busy"
            else:
                amb.event_status_type = None

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Ambulance]:
        result = await db.execute(
            select(Ambulance)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Ambulance.state),
                selectinload(Ambulance.lga),
                selectinload(Ambulance.ambulance_type)
            )
        )
        objs = list(result.scalars().all())
        await self._augment_busy_status(db, objs)
        return objs

    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        driver_name: Optional[str] = None,
        state_id: Optional[int] = None,
        ambulance_type_id: Optional[int] = None,
        days: Optional[int] = None
    ) -> Tuple[List[Ambulance], int]:
        query = select(Ambulance)
        
        if driver_name:
            query = query.filter(Ambulance.driver_name.ilike(f"%{driver_name}%"))
        if state_id:
            query = query.filter(Ambulance.state_id == state_id)
        if ambulance_type_id:
            query = query.filter(Ambulance.ambulance_type_id == ambulance_type_id)
        if days:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            query = query.filter(Ambulance.date_added >= start_date)

        # Get count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Get data
        result = await db.execute(
            query.order_by(Ambulance.date_added.desc())
            .options(
                selectinload(Ambulance.state),
                selectinload(Ambulance.lga),
                selectinload(Ambulance.ambulance_type)
            )
        )
        objs = list(result.scalars().all())
        await self._augment_busy_status(db, objs)
        return objs, total_count

    async def get_by_state(self, db: AsyncSession, state_id: int) -> List[Ambulance]:
        result = await db.execute(
            select(Ambulance)
            .filter(Ambulance.state_id == state_id)
            .order_by(Ambulance.date_added.desc())
            .options(
                selectinload(Ambulance.state),
                selectinload(Ambulance.lga),
                selectinload(Ambulance.ambulance_type)
            )
        )
        objs = list(result.scalars().all())
        await self._augment_busy_status(db, objs)
        return objs

    async def create(self, db: AsyncSession, *, obj_in: Any) -> Ambulance:
        obj_in_data = obj_in.model_dump(exclude_unset=True, by_alias=False)
        db_obj = Ambulance(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        # Re-fetch with eager-loaded relationships to avoid lazy load in async context
        result = await db.execute(
            select(Ambulance)
            .filter(Ambulance.id == db_obj.id)
            .options(
                selectinload(Ambulance.state),
                selectinload(Ambulance.lga),
                selectinload(Ambulance.ambulance_type)
            )
        )
        obj = result.scalars().first()
        if obj:
            await self._augment_busy_status(db, [obj])
        return obj



ambulance = CRUDAmbulance()
