from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate

class CRUDIncident:
    async def get(self, db: AsyncSession, id: int) -> Optional[Incident]:
        from app.models.patient import Patient as PatientModel
        from app.models.hospital import Hospital as HospitalModel
        from app.models.claim import Claim as ClaimModel
        result = await db.execute(
            select(Incident)
            .filter(Incident.id == id)
            .options(
                selectinload(Incident.patients).selectinload(PatientModel.interventions),
                selectinload(Incident.incident_type),
                selectinload(Incident.state),
                selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
                selectinload(Incident.hospital).selectinload(HospitalModel.state),
                selectinload(Incident.hospital).selectinload(HospitalModel.lga),
                selectinload(Incident.claims).selectinload(ClaimModel.images)
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
        from app.models.patient import Patient as PatientModel
        from app.models.hospital import Hospital as HospitalModel
        from app.models.claim import Claim as ClaimModel
        
        query = select(Incident).options(
            selectinload(Incident.patients).selectinload(PatientModel.interventions),
            selectinload(Incident.incident_type),
            selectinload(Incident.state),
            selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
            selectinload(Incident.hospital).selectinload(HospitalModel.state),
            selectinload(Incident.hospital).selectinload(HospitalModel.lga),
            selectinload(Incident.claims).selectinload(ClaimModel.images)
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

        # Count - optimized to run without subquery compilation
        count_q = select(func.count(Incident.id))
        if search:
            search_filter = or_(
                Incident.serial_no.ilike(f"%{search}%"),
                Incident.caller_name.ilike(f"%{search}%"),
                Incident.description.ilike(f"%{search}%")
            )
            count_q = count_q.filter(search_filter)
        if status:
            count_q = count_q.filter(Incident.incident_status_type == status)
        if triage:
            count_q = count_q.filter(Incident.triage_category == triage)
        if mass_casualty is not None:
            count_q = count_q.filter(Incident.mass_casualty == mass_casualty)
        if state_id_filter is not None:
            count_q = count_q.filter(Incident.state_id == state_id_filter)
        elif state_id is not None:
            count_q = count_q.filter(Incident.state_id == state_id)
        
        count_result = await db.execute(count_q)
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
        from app.core.socket_manager import SocketManager

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
        from app.models.hospital import Hospital as HospitalModel
        from app.models.claim import Claim as ClaimModel
        result = await db.execute(
            select(Incident)
            .filter(Incident.id == db_obj.id)
            .options(
                selectinload(Incident.patients).selectinload(PatientModel.interventions),
                selectinload(Incident.incident_type),
                selectinload(Incident.state),
                selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
                selectinload(Incident.hospital).selectinload(HospitalModel.state),
                selectinload(Incident.hospital).selectinload(HospitalModel.lga),
                selectinload(Incident.claims).selectinload(ClaimModel.images)
            )
        )
        final_obj = result.scalars().first()

        # BROADCAST: New Incident
        if final_obj and final_obj.state_id:
            await SocketManager.broadcast_incident_update(
                final_obj.state_id, 
                {
                    "type": "NEW_INCIDENT",
                    "incidentId": final_obj.id,
                    "serialNo": final_obj.serial_no,
                    "status": final_obj.incident_status_type,
                    "triage": final_obj.triage_category
                }
            )
        
        # PUSH NOTIFICATION: If ambulance is assigned
        if final_obj and final_obj.ambulance_id:
            try:
                from app.core.notifications import notification_service
                await notification_service.send_to_ambulance(
                    db, 
                    final_obj.ambulance_id, 
                    title="New Incident Assigned", 
                    body=f"Incident {final_obj.serial_no} has been assigned to your ambulance.",
                    data={"incidentId": final_obj.id, "type": "NEW_ASSIGNMENT"},
                    sound="incident_sound"
                )
            except Exception as e:
                print(f"[Notification Error] Failed to send push on creation: {e}")

        return final_obj

    async def update(self, db: AsyncSession, *, db_obj: Incident, obj_in: IncidentUpdate) -> Incident:
        from app.core.socket_manager import SocketManager
        
        old_ambulance_id = db_obj.ambulance_id
        
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Load relationships for the return
        from app.models.patient import Patient as PatientModel
        from app.models.hospital import Hospital as HospitalModel
        from app.models.claim import Claim as ClaimModel
        result = await db.execute(
            select(Incident)
            .filter(Incident.id == db_obj.id)
            .options(
                selectinload(Incident.patients).selectinload(PatientModel.interventions),
                selectinload(Incident.incident_type),
                selectinload(Incident.state),
                selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
                selectinload(Incident.hospital).selectinload(HospitalModel.state),
                selectinload(Incident.hospital).selectinload(HospitalModel.lga),
                selectinload(Incident.claims).selectinload(ClaimModel.images)
            )
        )
        final_obj = result.scalars().first()

        new_ambulance_id = final_obj.ambulance_id

        # BROADCAST: Updated Incident
        if final_obj and final_obj.state_id:
            await SocketManager.broadcast_incident_update(
                final_obj.state_id, 
                {
                    "type": "INCIDENT_UPDATE",
                    "incidentId": final_obj.id,
                    "status": final_obj.event_status_type or final_obj.incident_status_type,
                    "triage": final_obj.triage_category
                }
            )
        
        # PUSH NOTIFICATION: If ambulance was newly assigned or changed
        if final_obj and new_ambulance_id and new_ambulance_id != old_ambulance_id:
            try:
                from app.core.notifications import notification_service
                await notification_service.send_to_ambulance(
                    db, 
                    new_ambulance_id, 
                    title="New Incident Assignment", 
                    body=f"A new incident ({final_obj.serial_no}) has been assigned to you.",
                    data={"incidentId": final_obj.id, "type": "NEW_ASSIGNMENT"},
                    sound="incident_sound"
                )
            except Exception as e:
                print(f"[Notification Error] Failed to send push on update: {e}")
            
        return final_obj

    async def get_multi_by_ambulance(
        self,
        db: AsyncSession,
        *,
        ambulance_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Incident], int]:
        from app.models.patient import Patient as PatientModel
        from app.models.hospital import Hospital as HospitalModel
        from app.models.claim import Claim as ClaimModel
        
        query = select(Incident).filter(Incident.ambulance_id == ambulance_id).options(
            selectinload(Incident.patients).selectinload(PatientModel.interventions),
            selectinload(Incident.incident_type),
            selectinload(Incident.state),
            selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
            selectinload(Incident.hospital).selectinload(HospitalModel.state),
            selectinload(Incident.hospital).selectinload(HospitalModel.lga),
            selectinload(Incident.claims).selectinload(ClaimModel.images)
        ).order_by(Incident.date_added.desc())

        # Count - optimized to be extremely fast and avoid subquery compiling
        count_query = select(func.count(Incident.id)).filter(Incident.ambulance_id == ambulance_id)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Records
        result = await db.execute(
            query.offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

incident_crud = CRUDIncident()
