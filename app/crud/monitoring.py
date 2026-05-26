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
            by_nurtw_driver=obj_in.by_nurtw_driver,
            bls=obj_in.bls,
            labor_transportation=obj_in.labor_transportation,
            obstetric_transportation=obj_in.obstetric_transportation,
            neonatal_transportation=obj_in.neonatal_transportation,
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
                by_nurtw_driver=obj_in.by_nurtw_driver,
                bls=obj_in.bls,
                labor_transportation=obj_in.labor_transportation,
                obstetric_transportation=obj_in.obstetric_transportation,
                neonatal_transportation=obj_in.neonatal_transportation,
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
        stmt = select(
            Monitoring.month,
            func.sum(Monitoring.no_of_transport).label("noOfTransport"),
            func.sum(Monitoring.no_of_mamii_lgas).label("noOfMamiiLGAs"),
            func.sum(Monitoring.by_tricycle_ambulance).label("byTricycleAmbulance"),
            func.sum(Monitoring.by_nurtw_driver).label("byNurtwDriver"),
            func.sum(Monitoring.bls).label("bls"),
            func.sum(Monitoring.labor_transportation).label("laborTransportation"),
            func.sum(Monitoring.obstetric_transportation).label("obstetricTransportation"),
            func.sum(Monitoring.neonatal_transportation).label("neonatalTransportation"),
            func.sum(Monitoring.bemonc).label("bemonc"),
            func.sum(Monitoring.cemonc).label("cemonc"),
            func.sum(Monitoring.maternal_mortalities).label("maternalMortalities"),
            func.sum(Monitoring.neonatal_mortalities).label("neonatalMortalities"),
        ).group_by(Monitoring.month).order_by(Monitoring.month)
        
        if year:
            stmt = stmt.where(Monitoring.year == year)
        if state_id is not None:
            stmt = stmt.where(Monitoring.state_id == state_id)
            
        result = await db.execute(stmt)
        return result.all()

monitoring = CRUDMonitoring()
