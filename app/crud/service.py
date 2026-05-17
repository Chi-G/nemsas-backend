from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class CRUDService:
    async def get(self, db: AsyncSession, id: int) -> Optional[Service]:
        result = await db.execute(
            select(Service)
            .filter(Service.id == id)
            .options(selectinload(Service.fee_category))
        )
        return result.scalars().first()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Service]:
        result = await db.execute(
            select(Service)
            .options(selectinload(Service.fee_category))
            .order_by(Service.id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all_services(
        self, 
        db: AsyncSession, 
        *, 
        fee_category_id: Optional[int] = None, 
        is_medicine: Optional[bool] = None
    ) -> List[Service]:
        query = select(Service).options(selectinload(Service.fee_category))
        
        if fee_category_id is not None:
            query = query.filter(Service.fee_category_id == fee_category_id)
            
        if is_medicine is not None:
            from app.models.fee_category import FeeCategory
            query = query.join(FeeCategory).filter(FeeCategory.is_medicine == is_medicine)
            
        query = query.order_by(Service.id)
        result = await db.execute(query)
        return result.scalars().all()


    async def get_by_category(self, db: AsyncSession, *, fee_category_id: int) -> List[Service]:
        result = await db.execute(
            select(Service)
            .filter(Service.fee_category_id == fee_category_id)
            .options(selectinload(Service.fee_category))
            .order_by(Service.description)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: ServiceCreate) -> Service:
        db_obj = Service(
            id=obj_in.id,
            code=obj_in.code,
            description=obj_in.description,
            price=obj_in.price,
            fee_category_id=obj_in.fee_category_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Service, obj_in: ServiceUpdate) -> Service:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[Service]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

service_crud = CRUDService()
