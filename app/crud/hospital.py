from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Any
from app.models.hospital import Hospital
from app.schemas.hospital import HospitalCreate

class CRUDHospital:
    async def get(self, db: AsyncSession, id: Any) -> Optional[Hospital]:
        result = await db.execute(
            select(Hospital)
            .filter(Hospital.id == id)
            .options(
                selectinload(Hospital.hospital_type),
                selectinload(Hospital.state),
                selectinload(Hospital.lga)
            )
        )
        return result.scalars().first()

    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        name: Optional[str] = None,
        state_id: Optional[int] = None,
        days: Optional[int] = None
    ) -> tuple[List[Hospital], int]:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        query = select(Hospital)
        
        if name:
            query = query.filter(Hospital.name.ilike(f"%{name}%"))
        if state_id:
            query = query.filter(Hospital.state_id == state_id)
        if days:
            start_date = datetime.now() - timedelta(days=days)
            query = query.filter(Hospital.date_added >= start_date)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0


        result = await db.execute(
            query.offset(skip)
            .limit(limit)
            .options(
                selectinload(Hospital.hospital_type),
                selectinload(Hospital.state),
                selectinload(Hospital.lga)
            )
        )

        return result.scalars().all(), total

    async def create(self, db: AsyncSession, *, obj_in: HospitalCreate) -> Hospital:
        db_obj = Hospital(
            id=obj_in.id,
            name=obj_in.name,
            hospital_type_id=obj_in.hospital_type_id,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            location=obj_in.location,
            address1=obj_in.address1,
            address2=obj_in.address2,
            landmark=obj_in.landmark,
            nhia_or_shia=obj_in.nhia_or_shia,
            date_added=obj_in.date_added
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_state(self, db: AsyncSession, state_id: int) -> List[Hospital]:
        result = await db.execute(
            select(Hospital)
            .filter(Hospital.state_id == state_id)
            .options(
                selectinload(Hospital.hospital_type),
                selectinload(Hospital.state),
                selectinload(Hospital.lga)
            )
        )
        return result.scalars().all()

hospital_crud = CRUDHospital()
