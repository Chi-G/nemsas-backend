from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List, Optional
from app.models.monitoring import Monitoring
from app.schemas.monitoring import MonitoringCreate

class CRUDMonitoring:
    async def get_all(
        self, 
        db: AsyncSession, 
        *, 
        year: Optional[int] = None, 
        month: Optional[int] = None, 
        state_id: Optional[int] = None,
        remark: Optional[str] = None 
    ) -> List[Monitoring]:
        stmt = select(Monitoring).options(selectinload(Monitoring.state))
        if year is not None:
            stmt = stmt.filter(Monitoring.year == year)
        if month is not None:
            stmt = stmt.filter(Monitoring.month == month)
        if state_id is not None:
            stmt = stmt.filter(Monitoring.state_id == state_id)
        if remark is not None:
            stmt = stmt.filter(Monitoring.remark.ilike(f"%{remark}%"))
        result = await db.execute(stmt)
        return list(result.scalars().all())


    async def create(self, db: AsyncSession, *, obj_in: MonitoringCreate, added_by: Optional[str] = None) -> Monitoring:
        db_obj = Monitoring(
            year=obj_in.year,
            month=obj_in.month,
            no_of_transport=obj_in.no_of_transport,
            no_of_mamii_lgas=obj_in.no_of_mamii_lgas,
            by_tricycle_ambulance=obj_in.by_tricycle_ambulance,
            bls=obj_in.bls,
            als=obj_in.als,
            helicopters=obj_in.helicopters,
            community_volunteers=obj_in.community_volunteers,
            labor_transportation=obj_in.labor_transportation,
            obstetric_transportation=obj_in.obstetric_transportation,
            neonatal_transportation=obj_in.neonatal_transportation,
            paediatric_over_5=obj_in.paediatric_over_5,
            drowning=obj_in.drowning,
            snake_bite=obj_in.snake_bite,
            other_weapons=obj_in.other_weapons,
            gunshot=obj_in.gunshot,
            others=obj_in.others,
            paediatric_under_5=obj_in.paediatric_under_5,
            neonatal_under_5=obj_in.neonatal_under_5,
            obstetric_accident=obj_in.obstetric_accident,
            rta=obj_in.rta,
            bemonc=obj_in.bemonc,
            cemonc=obj_in.cemonc,
            maternal_mortalities=obj_in.maternal_mortalities,
            neonatal_mortalities=obj_in.neonatal_mortalities,
            remark=obj_in.remark,
            state_id=obj_in.state_id,
            added_by=added_by
        )
        db.add(db_obj)
        await db.commit()
        
        # Load with state relationship
        stmt = select(Monitoring).options(selectinload(Monitoring.state)).where(Monitoring.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalar_one()


    async def create_batch(self, db: AsyncSession, *, obj_list: List[MonitoringCreate], added_by: Optional[str] = None) -> List[Monitoring]:
        db_objs = []
        for obj_in in obj_list:
            db_obj = Monitoring(
                year=obj_in.year,
                month=obj_in.month,
                no_of_transport=obj_in.no_of_transport,
                no_of_mamii_lgas=obj_in.no_of_mamii_lgas,
                by_tricycle_ambulance=obj_in.by_tricycle_ambulance,
                bls=obj_in.bls,
                als=obj_in.als,
                helicopters=obj_in.helicopters,
                community_volunteers=obj_in.community_volunteers,
                labor_transportation=obj_in.labor_transportation,
                obstetric_transportation=obj_in.obstetric_transportation,
                neonatal_transportation=obj_in.neonatal_transportation,
                paediatric_over_5=obj_in.paediatric_over_5,
                drowning=obj_in.drowning,
                snake_bite=obj_in.snake_bite,
                other_weapons=obj_in.other_weapons,
                gunshot=obj_in.gunshot,
                others=obj_in.others,
                paediatric_under_5=obj_in.paediatric_under_5,
                neonatal_under_5=obj_in.neonatal_under_5,
                obstetric_accident=obj_in.obstetric_accident,
                rta=obj_in.rta,
                bemonc=obj_in.bemonc,
                cemonc=obj_in.cemonc,
                maternal_mortalities=obj_in.maternal_mortalities,
                neonatal_mortalities=obj_in.neonatal_mortalities,
                remark=obj_in.remark,
                state_id=obj_in.state_id,
                added_by=added_by
            )
            db.add(db_obj)
            db_objs.append(db_obj)
        await db.commit()
        
        # Load all created items with their state relationship
        ids = [o.id for o in db_objs]
        stmt = select(Monitoring).options(selectinload(Monitoring.state)).where(Monitoring.id.in_(ids))
        result = await db.execute(stmt)
        return list(result.scalars().all())


    async def get_monthly_aggregates(self, db: AsyncSession, year: Optional[int] = None, state_id: Optional[int] = None):
        base_stmt = select(
            Monitoring.month,
            func.coalesce(func.sum(Monitoring.no_of_transport), 0).label("noOfTransport"),
            func.coalesce(func.sum(Monitoring.no_of_mamii_lgas), 0).label("noOfMamiiLGAs"),
            func.coalesce(func.sum(Monitoring.by_tricycle_ambulance), 0).label("byTricycleAmbulance"),
            func.coalesce(func.sum(Monitoring.bls), 0).label("bls"),
            func.coalesce(func.sum(Monitoring.als), 0).label("als"),
            func.coalesce(func.sum(Monitoring.helicopters), 0).label("helicopters"),
            func.coalesce(func.sum(Monitoring.community_volunteers), 0).label("communityVolunteers"),
            func.coalesce(func.sum(Monitoring.labor_transportation), 0).label("laborTransportation"),
            func.coalesce(func.sum(Monitoring.obstetric_transportation), 0).label("obstetricTransportation"),
            func.coalesce(func.sum(Monitoring.neonatal_transportation), 0).label("neonatalTransportation"),
            func.coalesce(func.sum(Monitoring.paediatric_over_5), 0).label("paediatricOver5"),
            func.coalesce(func.sum(Monitoring.drowning), 0).label("drowning"),
            func.coalesce(func.sum(Monitoring.snake_bite), 0).label("snakeBite"),
            func.coalesce(func.sum(Monitoring.other_weapons), 0).label("otherWeapons"),
            func.coalesce(func.sum(Monitoring.gunshot), 0).label("gunshot"),
            func.coalesce(func.sum(Monitoring.others), 0).label("others"),
            func.coalesce(func.sum(Monitoring.paediatric_under_5), 0).label("paediatricUnder5"),
            func.coalesce(func.sum(Monitoring.neonatal_under_5), 0).label("neonatalUnder5"),
            func.coalesce(func.sum(Monitoring.obstetric_accident), 0).label("obstetricAccident"),
            func.coalesce(func.sum(Monitoring.rta), 0).label("rta"),
            func.coalesce(func.sum(Monitoring.bemonc), 0).label("bemonc"),
            func.coalesce(func.sum(Monitoring.cemonc), 0).label("cemonc"),
            func.coalesce(func.sum(Monitoring.maternal_mortalities), 0).label("maternalMortalities"),
            func.coalesce(func.sum(Monitoring.neonatal_mortalities), 0).label("neonatalMortalities"),
        ).group_by(Monitoring.month).order_by(Monitoring.month)

        if year:
            base_stmt = base_stmt.where(Monitoring.year == year)

        if state_id is not None:
            # 1st priority: state-specific records
            rows = (await db.execute(base_stmt.where(Monitoring.state_id == state_id))).all()
            if rows:
                return rows
            # 2nd priority: national records (state_id IS NULL)
            rows = (await db.execute(base_stmt.where(Monitoring.state_id.is_(None)))).all()
            if rows:
                return rows
            # 3rd priority: all available records (no state-specific or national data exists yet)
            result = await db.execute(base_stmt)
            return result.all()

        # No state filter — aggregate all records
        result = await db.execute(base_stmt)
        return result.all()

    async def get(self, db: AsyncSession, *, id: int):
        """Get a single monitoring record by ID."""
        stmt = select(Monitoring).options(selectinload(Monitoring.state)).where(Monitoring.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def update(self, db: AsyncSession, *, db_obj: Monitoring, obj_in) -> Monitoring:
        """Partially update a monitoring record."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        # Reload with state
        stmt = select(Monitoring).options(selectinload(Monitoring.state)).where(Monitoring.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def remove(self, db: AsyncSession, *, id: int):
        """Delete a monitoring record by ID."""
        stmt = select(Monitoring).where(Monitoring.id == id)
        result = await db.execute(stmt)
        db_obj = result.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

monitoring = CRUDMonitoring()
