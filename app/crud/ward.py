from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.ward import Ward
from app.schemas.ward import WardCreate

class CRUDWard:
    async def get_all(self, db: AsyncSession) -> List[Ward]:
        result = await db.execute(select(Ward).order_by(Ward.name))
        return result.scalars().all()

    async def get_by_lga(self, db: AsyncSession, *, lga_id: int) -> List[Ward]:
        result = await db.execute(select(Ward).filter(Ward.lga_id == lga_id).order_by(Ward.name))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: WardCreate) -> Ward:
        db_obj = Ward(
            id=obj_in.id,
            name=obj_in.name,
            code=obj_in.code,
            lga_id=obj_in.lga_id,
            date_added=obj_in.date_added
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

ward_crud = CRUDWard()
