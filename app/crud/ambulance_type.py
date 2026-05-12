from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Any
from app.models.ambulance_type import AmbulanceType
from app.schemas.ambulance_type import AmbulanceTypeCreate

class CRUDAmbulanceType:
    async def get(self, db: AsyncSession, id: Any) -> Optional[AmbulanceType]:
        result = await db.execute(select(AmbulanceType).filter(AmbulanceType.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[AmbulanceType]:
        result = await db.execute(select(AmbulanceType).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: AmbulanceTypeCreate) -> AmbulanceType:
        db_obj = AmbulanceType(
            id=obj_in.id,
            name=obj_in.name,
            description=obj_in.description,
            date_added=obj_in.date_added
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

ambulance_type_crud = CRUDAmbulanceType()
