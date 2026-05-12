from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.run_sheet import RunSheet
from app.models.user import User

class CRUDRunSheet:
    async def get_multi_with_count(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Tuple[List[RunSheet], int]:
        stmt = select(RunSheet).options(
            selectinload(RunSheet.medic_user).selectinload(User.state),
            selectinload(RunSheet.medic_user).selectinload(User.lga),
            selectinload(RunSheet.medic_user).selectinload(User.ward),
        ).order_by(desc(RunSheet.id))
        count_stmt = select(func.count()).select_from(RunSheet)
        
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

run_sheet = CRUDRunSheet()
