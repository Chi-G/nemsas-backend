from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate

class CRUDIncident:
    async def get(self, db: AsyncSession, id: int) -> Optional[Incident]:
        result = await db.execute(
            select(Incident)
            .filter(Incident.id == id)
            .options(
                selectinload(Incident.patients),
                selectinload(Incident.incident_type),
                selectinload(Incident.state)
            )
        )
        return result.scalars().first()

    async def get_multi_with_count(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        triage: Optional[str] = None,
        state_id: Optional[int] = None,
        state_id_filter: Optional[int] = None,
        mass_casualty: Optional[bool] = None,
        incident_category_id: Optional[int] = None,
        sort_by_state: bool = False
    ) -> Tuple[List[Incident], int]:
        query = select(Incident).options(
            selectinload(Incident.patients),
            selectinload(Incident.incident_type),
            selectinload(Incident.state)
        )

        if search:
            search_filter = or_(
                Incident.serial_no.ilike(f"%{search}%"),
                Incident.caller_name.ilike(f"%{search}%"),
                Incident.caller_number.ilike(f"%{search}%"),
                Incident.description.ilike(f"%{search}%"),
                Incident.incident_location.ilike(f"%{search}%"),
                Incident.street.ilike(f"%{search}%"),
                Incident.district_ward.ilike(f"%{search}%"),
                Incident.area_council.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        if status:
            query = query.filter(Incident.incident_status_type == status)
        if triage:
            query = query.filter(Incident.triage_category == triage)
        if mass_casualty is not None:
            query = query.filter(Incident.mass_casualty == mass_casualty)
        if incident_category_id is not None:
            query = query.filter(Incident.incident_category_id == incident_category_id)
        
        # Priority for strict state filtering (from role)
        if state_id_filter is not None:
            query = query.filter(Incident.state_id == state_id_filter)
        elif state_id is not None:
            query = query.filter(Incident.state_id == state_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Sorting
        if sort_by_state:
            # We sort by state_name
            query = query.order_by(Incident.state_name.asc())
        else:
            query = query.order_by(Incident.date_added.desc())

        # Records
        result = await db.execute(
            query.offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, db: AsyncSession, *, obj_in: IncidentCreate) -> Incident:
        from app.models.patient import Patient as PatientModel
        import string
        import random
        from datetime import datetime

        # Generate serial number if not provided
        serial_no = obj_in.serial_no
        if not serial_no:
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            now = datetime.now()
            serial_no = f"IND-{random_str}-{now.strftime('%d-%m-%Y %H:%M')} +00"

        # Prepare incident data
        incident_data = obj_in.model_dump(exclude={"patients", "incident_category", "ambulance_type", "ambulance_name"})
        incident_data["serial_no"] = serial_no
        
        # Set default status if not provided
        if not incident_data.get("incident_status_type"):
            incident_data["incident_status_type"] = "Reported"
        
        if not incident_data.get("date_added"):
            incident_data["date_added"] = datetime.now()

        db_obj = Incident(**incident_data)
        db.add(db_obj)
        await db.flush() # Flush to get the incident ID

        # Create patients
        for patient_in in obj_in.patients:
            patient_data = patient_in.model_dump()
            patient_data["incident_id"] = db_obj.id
            db_patient = PatientModel(**patient_data)
            db.add(db_patient)

        await db.commit()
        await db.refresh(db_obj)
        
        # Load relationships for the return
        result = await db.execute(
            select(Incident)
            .filter(Incident.id == db_obj.id)
            .options(
                selectinload(Incident.patients),
                selectinload(Incident.incident_type)
            )
        )
        return result.scalars().first()

incident_crud = CRUDIncident()
