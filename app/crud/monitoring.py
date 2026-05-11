from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from app.models.monitoring import Monitoring

class CRUDMonitoring:
    async def get_all(self, db: AsyncSession) -> List[Monitoring]:
        stmt = select(Monitoring).options(selectinload(Monitoring.state))
        result = await db.execute(stmt)
        return list(result.scalars().all())

monitoring = CRUDMonitoring()
