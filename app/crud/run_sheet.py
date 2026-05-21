from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.run_sheet import RunSheet
from app.models.user import User
from uuid import UUID

from app.models.incident import Incident
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.claim import Claim
from app.models.patient import Patient

class CRUDRunSheet:
    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        medic_user_id: Optional[UUID] = None,
        ambulance_id: Optional[int] = None,
        state_id: Optional[int] = None
    ) -> Tuple[List[RunSheet], int]:
        stmt = select(RunSheet).options(
            selectinload(RunSheet.medic_user).selectinload(User.state),
            selectinload(RunSheet.medic_user).selectinload(User.lga),
            selectinload(RunSheet.medic_user).selectinload(User.ward),
            selectinload(RunSheet.incident).selectinload(Incident.patients),
            selectinload(RunSheet.incident).selectinload(Incident.claims).selectinload(Claim.images),
            selectinload(RunSheet.incident).selectinload(Incident.hospital).selectinload(Hospital.state),
            selectinload(RunSheet.incident).selectinload(Incident.hospital).selectinload(Hospital.lga),
            selectinload(RunSheet.incident).selectinload(Incident.hospital).selectinload(Hospital.hospital_type),
            selectinload(RunSheet.incident).selectinload(Incident.state),
            selectinload(RunSheet.patient).selectinload(Patient.interventions),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.state),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.lga),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.ward),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.ambulance_type)
        ).order_by(desc(RunSheet.id))
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
            
        if base_filters:
            stmt = stmt.where(*base_filters)
            count_stmt = count_stmt.where(*base_filters)
            
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

run_sheet = CRUDRunSheet()
