from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Any
from app.models.hospital_type import HospitalType
from app.schemas.hospital_type import HospitalTypeCreate

class CRUDHospitalType:
    async def get(self, db: AsyncSession, id: Any) -> Optional[HospitalType]:
        result = await db.execute(select(HospitalType).filter(HospitalType.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[HospitalType]:
        result = await db.execute(select(HospitalType).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: HospitalTypeCreate) -> HospitalType:
        db_obj = HospitalType(
            id=obj_in.id,
            name=obj_in.name,
            description=obj_in.description,
            date_added=obj_in.date_added
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

hospital_type_crud = CRUDHospitalType()
