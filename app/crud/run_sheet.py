from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_, exists, extract
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
        state_id: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        incident_category_id: Optional[int] = None,
        patient_name: Optional[str] = None
    ) -> Tuple[List[RunSheet], int]:
        stmt = select(RunSheet).options(*self._get_runsheet_options()).order_by(desc(RunSheet.id))
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
            
        if month is not None:
            base_filters.append(extract('month', RunSheet.created_at) == month)
            
        if year is not None:
            base_filters.append(extract('year', RunSheet.created_at) == year)
            
        if incident_category_id is not None:
            stmt = stmt.join(RunSheet.incident)
            count_stmt = count_stmt.join(RunSheet.incident)
            base_filters.append(Incident.incident_category_id == incident_category_id)
            
        if patient_name:
            search_pattern = f"%{patient_name}%"
            from sqlalchemy import cast, String
            patient_exists = exists().where(
                or_(
                    (cast(RunSheet.patient_id, String).ilike(func.concat('%', cast(Patient.id, String), '%'))) & (
                        func.concat(func.coalesce(Patient.first_name, ''), ' ', func.coalesce(Patient.last_name, '')).ilike(search_pattern) |
                        Patient.first_name.ilike(search_pattern) |
                        Patient.last_name.ilike(search_pattern)
                    ),
                    (Patient.incident_id == RunSheet.incident_id) & (
                        func.concat(func.coalesce(Patient.first_name, ''), ' ', func.coalesce(Patient.last_name, '')).ilike(search_pattern) |
                        Patient.first_name.ilike(search_pattern) |
                        Patient.last_name.ilike(search_pattern)
                    )
                )
            )
            base_filters.append(
                or_(
                    RunSheet.patient_name.ilike(search_pattern),
                    patient_exists
                )
            )
            
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
            selectinload(RunSheet.incident).selectinload(Incident.incident_type),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.state),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.lga),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.ward),
            selectinload(RunSheet.ambulance).selectinload(Ambulance.ambulance_type)
        ]

    async def create(self, db: AsyncSession, *, obj_in: RunSheetCreate) -> RunSheet:
        obj_in_data = obj_in.model_dump(exclude_none=True, by_alias=False)
        obj_in_data.pop("emergency_treatment_center_id", None)
        obj_in_data.pop("price", None)
        obj_in_data.pop("user_id", None)
        
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
                
                # Proactively load patients if patient_id is not provided
                if "patient_id" not in obj_in_data or not obj_in_data["patient_id"]:
                    patient_stmt = select(Patient).where(Patient.incident_id == incident_id)
                    patient_res = await db.execute(patient_stmt)
                    patient_objs = patient_res.scalars().all()
                    if patient_objs:
                        first_patient = patient_objs[0]
                        obj_in_data["patient_id"] = first_patient.id
                        if "patient_name" not in obj_in_data or not obj_in_data["patient_name"]:
                            full_name = f"{first_patient.first_name or ''} {first_patient.middle_name or ''} {first_patient.last_name or ''}".strip()
                            obj_in_data["patient_name"] = full_name if full_name else "Unknown Patient"
                        if "age" not in obj_in_data or not obj_in_data["age"]:
                            if first_patient.do_b:
                                from datetime import datetime
                                obj_in_data["age"] = datetime.now().year - first_patient.do_b.year
                        if "gender" not in obj_in_data or not obj_in_data["gender"]:
                            if first_patient.sex == 1:
                                obj_in_data["gender"] = "Male"
                            elif first_patient.sex == 2:
                                obj_in_data["gender"] = "Female"

        db_obj = RunSheet(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        
        stmt = select(RunSheet).options(*self._get_runsheet_options()).where(RunSheet.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

run_sheet = CRUDRunSheet()
