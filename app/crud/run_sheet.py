from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.run_sheet import RunSheet
from app.models.user import User
from uuid import UUID

class CRUDRunSheet:
    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        medic_user_id: Optional[UUID] = None,
        ambulance_id: Optional[int] = None,
        state_id: Optional[int] = None,
        exclude_null_incident: bool = False,
        load_medic_user: bool = True
    ) -> Tuple[List[RunSheet], int]:
        stmt = select(RunSheet).options(
            selectinload(RunSheet.incident),
            selectinload(RunSheet.emergency_treatment_center),
        )
        if load_medic_user:
            stmt = stmt.options(
                selectinload(RunSheet.medic_user).selectinload(User.state),
                selectinload(RunSheet.medic_user).selectinload(User.lga),
                selectinload(RunSheet.medic_user).selectinload(User.ward),
            )
        stmt = stmt.order_by(desc(RunSheet.id))
        count_stmt = select(func.count()).select_from(RunSheet)
        
        base_filters = []
        
        if medic_user_id is not None:
            base_filters.append(RunSheet.medic_user_id == medic_user_id)
            
        if ambulance_id is not None:
            base_filters.append(RunSheet.ambulance_id == ambulance_id)
            
        if state_id is not None:
            stmt = stmt.join(RunSheet.medic_user)
            count_stmt = count_stmt.join(RunSheet.medic_user)
            base_filters.append(User.state_id == state_id)
            
        if exclude_null_incident:
            base_filters.append(RunSheet.incident_id.is_not(None))
            
        if base_filters:
            stmt = stmt.where(*base_filters)
            count_stmt = count_stmt.where(*base_filters)
            
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

    async def create(self, db: AsyncSession, *, obj_in: Any) -> RunSheet:
        obj_in_data = obj_in.model_dump(exclude_unset=True, by_alias=False)
        db_obj = RunSheet(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Refresh with relationships
        stmt = select(RunSheet).options(
            selectinload(RunSheet.medic_user).selectinload(User.state),
            selectinload(RunSheet.medic_user).selectinload(User.lga),
            selectinload(RunSheet.medic_user).selectinload(User.ward),
            selectinload(RunSheet.incident),
            selectinload(RunSheet.emergency_treatment_center),
        ).where(RunSheet.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get(self, db: AsyncSession, id: Any, load_medic_user: bool = True) -> Optional[RunSheet]:
        stmt = select(RunSheet).options(
            selectinload(RunSheet.incident),
            selectinload(RunSheet.emergency_treatment_center),
        )
        if load_medic_user:
            stmt = stmt.options(
                selectinload(RunSheet.medic_user).selectinload(User.state),
                selectinload(RunSheet.medic_user).selectinload(User.lga),
                selectinload(RunSheet.medic_user).selectinload(User.ward),
            )
        stmt = stmt.where(RunSheet.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

run_sheet = CRUDRunSheet()
