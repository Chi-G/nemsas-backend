from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate

class CRUDRole:
    async def get(self, db: AsyncSession, id: str) -> Optional[Role]:
        result = await db.execute(select(Role).filter(Role.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Role]:
        result = await db.execute(select(Role).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        db_obj = Role(id=obj_in.id, name=obj_in.name)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj 

    async def update(self, db: AsyncSession, *, db_obj: Role, obj_in: RoleUpdate) -> Role:
        db_obj.name = obj_in.name
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: str) -> Optional[Role]:
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

role_crud = CRUDRole()

