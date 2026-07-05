from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.claim_setting import ClaimSetting

class CRUDClaimSetting:
    async def get_all(self, db: AsyncSession) -> List[ClaimSetting]:
        result = await db.execute(select(ClaimSetting))
        return list(result.scalars().all())

    async def get_by_key(self, db: AsyncSession, key: str) -> ClaimSetting | None:
        result = await db.execute(select(ClaimSetting).where(ClaimSetting.key == key))
        return result.scalars().first()
        
    async def create_or_update(self, db: AsyncSession, *, obj_in, user_id=None) -> ClaimSetting:
        existing = await self.get_by_key(db, obj_in.key)
        if existing:
            existing.value = obj_in.value
            if user_id:
                existing.updated_by_id = user_id
            db.add(existing)
            await db.commit()
            # Removed db.refresh to prevent TimeoutError / deadlocks
            return existing
        else:
            new_setting = ClaimSetting(
                key=obj_in.key,
                value=obj_in.value,
                updated_by_id=user_id
            )
            db.add(new_setting)
            await db.commit()
            return new_setting

claim_setting = CRUDClaimSetting()
