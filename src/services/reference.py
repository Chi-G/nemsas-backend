from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from src.db.models.reference import (
    Drug, State, LGA, AmbulanceType, AccreditationCategory, SystemAuditLog
)
from src.schemas.reference import (
    DrugCreate, DrugUpdate, AmbulanceTypeCreate, AccreditationCategoryCreate
)
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

class ReferenceService:
    @staticmethod
    async def log_audit(
        db: AsyncSession, 
        user_id: int, 
        table_name: str, 
        record_id: int, 
        action: str, 
        changes: Optional[Dict] = None
    ):
        audit = SystemAuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            changes=changes,
            user_id=user_id
        )
        db.add(audit)

    @staticmethod
    async def get_state_lga_hierarchy(db: AsyncSession) -> List[State]:
        stmt = select(State).options(selectinload(State.lgas)).order_by(State.name)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_drug(db: AsyncSession, obj_in: DrugCreate, user_id: int) -> Drug:
        db_obj = Drug(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        
        await ReferenceService.log_audit(db, user_id, "drugs", db_obj.id, "CREATE", obj_in.model_dump())
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_drug(db: AsyncSession, drug_id: int, obj_in: DrugUpdate, user_id: int) -> Optional[Drug]:
        stmt = select(Drug).where(Drug.id == drug_id)
        result = await db.execute(stmt)
        db_obj = result.scalars().first()
        if not db_obj:
            return None
            
        update_data = obj_in.model_dump(exclude_unset=True)
        changes = {}
        for field, value in update_data.items():
            old_val = getattr(db_obj, field)
            if old_val != value:
                changes[field] = {"old": old_val, "new": value}
                setattr(db_obj, field, value)
        
        if changes:
            action = "DEACTIVATE" if update_data.get("is_active") is False else "UPDATE"
            await ReferenceService.log_audit(db, user_id, "drugs", drug_id, action, changes)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def create_ambulance_type(db: AsyncSession, obj_in: AmbulanceTypeCreate, user_id: int) -> AmbulanceType:
        db_obj = AmbulanceType(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await ReferenceService.log_audit(db, user_id, "ambulance_types", db_obj.id, "CREATE", obj_in.model_dump())
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def create_accreditation_category(db: AsyncSession, obj_in: AccreditationCategoryCreate, user_id: int) -> AccreditationCategory:
        db_obj = AccreditationCategory(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await ReferenceService.log_audit(db, user_id, "accreditation_categories", db_obj.id, "CREATE", obj_in.model_dump())
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

reference_service = ReferenceService()
