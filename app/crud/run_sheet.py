from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple, Any
from app.models.run_sheet import RunSheet
from app.models.user import User
from uuid import UUID

from app.models.incident import Incident
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.claim import Claim
from app.models.patient import Patient
from app.schemas.run_sheet import RunSheetCreate

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

    def _get_runsheet_options(self) -> List[Any]:
        return [
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
        ]

    async def create(self, db: AsyncSession, *, obj_in: RunSheetCreate) -> RunSheet:
        obj_in_data = obj_in.model_dump(exclude_none=True, by_alias=False)
        obj_in_data.pop("emergency_treatment_center_id", None)
        obj_in_data.pop("price", None)
        
        incident_id = obj_in_data.get("incident_id")
        if incident_id:
            incident_stmt = select(Incident).where(Incident.id == incident_id)
            incident_res = await db.execute(incident_stmt)
            incident_obj = incident_res.scalars().first()
            if incident_obj:
                if "route_from" not in obj_in_data or not obj_in_data["route_from"]:
                    obj_in_data["route_from"] = incident_obj.incident_location or "Fct zone2"
                if "route_to" not in obj_in_data or not obj_in_data["route_to"]:
                    hospital_stmt = select(Hospital).where(Hospital.id == incident_obj.hospital_id)
                    hospital_res = await db.execute(hospital_stmt)
                    hospital_obj = hospital_res.scalars().first()
                    if hospital_obj:
                        obj_in_data["route_to"] = hospital_obj.name or "Hospital"
                    else:
                        obj_in_data["route_to"] = "Hospital"

        db_obj = RunSheet(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        
        stmt = select(RunSheet).options(*self._get_runsheet_options()).where(RunSheet.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

run_sheet = CRUDRunSheet()
