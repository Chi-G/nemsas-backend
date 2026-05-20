from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.role import Role
from app.schemas.role import RoleCreate

class CRUDRole:
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Role]:
        result = await db.execute(select(Role).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        db_obj = Role(id=obj_in.id, name=obj_in.name)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj 

role_crud = CRUDRole()
