from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.claim_setting import ClaimSetting

class CRUDClaimSetting:
    async def get_all(self, db: AsyncSession) -> List[ClaimSetting]:
        result = await db.execute(select(ClaimSetting))
        return list(result.scalars().all())

claim_setting = CRUDClaimSetting()
