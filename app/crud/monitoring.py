from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List, Optional
from app.models.monitoring import Monitoring

class CRUDMonitoring:
    async def get_all(
        self, 
        db: AsyncSession, 
        *, 
        year: Optional[int] = None, 
        month: Optional[int] = None, 
        state_id: Optional[int] = None
    ) -> List[Monitoring]:
        stmt = select(Monitoring).options(selectinload(Monitoring.state))
        if year is not None:
            stmt = stmt.filter(Monitoring.year == year)
        if month is not None:
            stmt = stmt.filter(Monitoring.month == month)
        if state_id is not None:
            stmt = stmt.filter(Monitoring.state_id == state_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())


    async def get_monthly_aggregates(self, db: AsyncSession, year: Optional[int] = None):
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
            
        result = await db.execute(stmt)
        return result.all()

monitoring = CRUDMonitoring()
