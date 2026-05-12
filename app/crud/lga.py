from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.lga import LGA
from app.schemas.lga import LGACreate

class CRUDLGA:
    async def get_all(self, db: AsyncSession) -> List[LGA]:
        result = await db.execute(select(LGA).order_by(LGA.name))
        return result.scalars().all()

    async def get_by_state(self, db: AsyncSession, *, state_id: int) -> List[LGA]:
        result = await db.execute(select(LGA).filter(LGA.state_id == state_id).order_by(LGA.name))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: LGACreate) -> LGA:
        db_obj = LGA(
            id=obj_in.id,
            name=obj_in.name,
            code=obj_in.code,
            state_id=obj_in.state_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

lga_crud = CRUDLGA()
