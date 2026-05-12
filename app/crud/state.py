from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.state import State
from app.schemas.state import StateCreate

class CRUDState:
    async def get_all(self, db: AsyncSession) -> List[State]:
        result = await db.execute(select(State).order_by(State.name))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: StateCreate) -> State:
        db_obj = State(
            id=obj_in.id,
            name=obj_in.name,
            code=obj_in.code
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

state_crud = CRUDState()
