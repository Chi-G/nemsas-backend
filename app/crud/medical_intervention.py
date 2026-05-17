from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional, Tuple
from app.models.medical_intervention import MedicalIntervention
from app.schemas.medical_intervention import MedicalInterventionCreate, MedicalInterventionUpdate

class CRUDMedicalIntervention:
    async def get(self, db: AsyncSession, id: int) -> Optional[MedicalIntervention]:
        result = await db.execute(
            select(MedicalIntervention).filter(MedicalIntervention.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, patient_id: Optional[int] = None
    ) -> List[MedicalIntervention]:
        query = select(MedicalIntervention)
        if patient_id:
            query = query.filter(MedicalIntervention.patient_id == patient_id)
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: MedicalInterventionCreate) -> MedicalIntervention:
        obj_in_data = obj_in.model_dump()
        db_obj = MedicalIntervention(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: MedicalIntervention, obj_in: MedicalInterventionUpdate
    ) -> MedicalIntervention:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> MedicalIntervention:
        result = await db.execute(select(MedicalIntervention).filter(MedicalIntervention.id == id))
        obj = result.scalars().first()
        await db.delete(obj)
        await db.commit()
        return obj

medical_intervention_crud = CRUDMedicalIntervention()
