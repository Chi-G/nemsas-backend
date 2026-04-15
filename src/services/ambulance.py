from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.db.models.ambulance import Ambulance, GPSHistory, AmbulanceStatus, Dispatch, IncidentLeg, AccreditationType
from src.db.models.partner import Pledge, Partner, Facility, PledgeStatus
from src.schemas.ambulance import (
    AmbulanceCreate, AmbulanceUpdate, GPSHistoryCreate, 
    BulkUploadReport, BulkUploadRowReport, FleetFilter
)
from typing import List, Optional, Any, Dict
import math
import csv
import io
from datetime import datetime, timezone, date

class AmbulanceService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: AmbulanceCreate) -> Ambulance:
        # Check for unique plate number
        stmt = select(Ambulance).where(Ambulance.plate_number == obj_in.plate_number)
        result = await db.execute(stmt)
        if result.scalars().first():
            raise ValueError(f"Ambulance with plate number {obj_in.plate_number} already exists")

        db_obj = Ambulance(
            plate_number=obj_in.plate_number,
            make_model=obj_in.make_model,
            year=obj_in.year,
            accreditation_type=obj_in.accreditation_type,
            fuel_type=obj_in.fuel_type,
            capacity=obj_in.capacity,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            partner_id=obj_in.partner_id,
            equipment=obj_in.equipment,
            roadworthiness_expiry=obj_in.roadworthiness_expiry,
            insurance_expiry=obj_in.insurance_expiry,
            status=AmbulanceStatus.ACTIVE,
        )
        db.add(db_obj)
        
        # Pledge Fulfillment Logic
        if obj_in.partner_id:
            # Find the first pending or in-progress pledge for this partner in this state
            pledge_stmt = select(Pledge).join(Partner).where(
                Partner.user_id == obj_in.partner_id,
                Pledge.target_state_id == obj_in.state_id,
                Pledge.status.in_([PledgeStatus.PENDING, PledgeStatus.IN_PROGRESS])
            ).order_by(Pledge.created_at.asc())
            
            pledge_result = await db.execute(pledge_stmt)
            pledge = pledge_result.scalars().first()
            
            if pledge:
                pledge.fulfilled_count += 1
                if pledge.fulfilled_count >= pledge.ambulance_count:
                    pledge.status = PledgeStatus.FULFILLED
                else:
                    pledge.status = PledgeStatus.IN_PROGRESS

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, ambulance_id: int, state_id: Optional[int] = None) -> Optional[Ambulance]:
        stmt = select(Ambulance).where(Ambulance.id == ambulance_id)
        if state_id:
            stmt = stmt.where(Ambulance.state_id == state_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def list_ambulances(
        db: AsyncSession, filters: FleetFilter, skip: int = 0, limit: int = 100, state_id: Optional[int] = None
    ) -> List[Ambulance]:
        stmt = select(Ambulance)
        
        if state_id:
            stmt = stmt.where(Ambulance.state_id == state_id)
        elif filters.state_id:
            stmt = stmt.where(Ambulance.state_id == filters.state_id)
            
        if filters.lga_id:
            stmt = stmt.where(Ambulance.lga_id == filters.lga_id)
        if filters.status:
            stmt = stmt.where(Ambulance.status == filters.status)
        if filters.accreditation_type:
            stmt = stmt.where(Ambulance.accreditation_type == filters.accreditation_type)
        if filters.partner_id:
            stmt = stmt.where(Ambulance.partner_id == filters.partner_id)
        if filters.facility_id:
            stmt = stmt.where(Ambulance.facility_id == filters.facility_id)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def bulk_validate_csv(db: AsyncSession, csv_content: str, partner_id: Optional[int] = None) -> BulkUploadReport:
        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)
        
        reports = []
        passed = 0
        failed = 0
        
        for i, row in enumerate(reader, start=1):
            errors = []
            try:
                # Basic validation
                plate = row.get("plate_number")
                if not plate:
                    errors.append("Plate number is required")
                else:
                    # Check uniqueness in DB (async check inside loop is slow but safer for validation stage)
                    stmt = select(Ambulance).where(Ambulance.plate_number == plate)
                    res = await db.execute(stmt)
                    if res.scalars().first():
                        errors.append(f"Plate number {plate} already exists")
                
                if not row.get("make_model"): errors.append("Make/Model is required")
                if not row.get("year"): errors.append("Year is required")
                if not row.get("accreditation_type"): errors.append("Accreditation type is required")
                if not row.get("state_id"): errors.append("State ID is required")
                if not row.get("lga_id"): errors.append("LGA ID is required")
                
                is_valid = len(errors) == 0
                if is_valid:
                    passed += 1
                else:
                    failed += 1
                
                reports.append(BulkUploadRowReport(
                    row_number=i,
                    plate_number=plate or "N/A",
                    is_valid=is_valid,
                    errors=errors,
                    data=row if is_valid else None
                ))
            except Exception as e:
                failed += 1
                reports.append(BulkUploadRowReport(
                    row_number=i,
                    plate_number=row.get("plate_number", "UNKNOWN"),
                    is_valid=False,
                    errors=[str(e)]
                ))

        return BulkUploadReport(
            total_rows=len(reports),
            passed_rows=passed,
            failed_rows=failed,
            reports=reports
        )

    @staticmethod
    async def bulk_commit(db: AsyncSession, data_list: List[Dict[str, Any]], partner_id: Optional[int] = None) -> List[Ambulance]:
        created = []
        for data in data_list:
            # We assume data is already validated via bulk_validate_csv
            # Convert string dates if present
            rw_expiry = data.get("roadworthiness_expiry")
            ins_expiry = data.get("insurance_expiry")
            
            obj_in = AmbulanceCreate(
                plate_number=data["plate_number"],
                make_model=data["make_model"],
                year=int(data["year"]),
                accreditation_type=AccreditationType(data["accreditation_type"]),
                fuel_type=data.get("fuel_type"),
                capacity=int(data.get("capacity", 1)),
                state_id=int(data["state_id"]),
                lga_id=int(data["lga_id"]),
                partner_id=partner_id or (int(data["partner_id"]) if data.get("partner_id") else None),
                equipment=data.get("equipment"),
                roadworthiness_expiry=date.fromisoformat(rw_expiry) if rw_expiry else None,
                insurance_expiry=date.fromisoformat(ins_expiry) if ins_expiry else None
            )
            amb = await AmbulanceService.create(db, obj_in)
            created.append(amb)
        return created

    @staticmethod
    def generate_csv_template() -> str:
        output = io.StringIO()
        headers = [
            "plate_number", "make_model", "year", "accreditation_type", 
            "fuel_type", "capacity", "state_id", "lga_id", "partner_id",
            "equipment", "roadworthiness_expiry", "insurance_expiry"
        ]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        # Add guidance row as requested: "guidance notes in the first row"
        # Wait, usually template has one row of sample/guidance.
        writer.writerow({
            "plate_number": "ABC-123-XY (Unique)",
            "make_model": "Toyota Hiace",
            "year": "2022",
            "accreditation_type": "BLS or ALS",
            "fuel_type": "Petrol/Diesel",
            "capacity": "1",
            "state_id": "1",
            "lga_id": "1",
            "partner_id": "Optional",
            "equipment": "Oxygen, Stretcher, etc.",
            "roadworthiness_expiry": "YYYY-MM-DD",
            "insurance_expiry": "YYYY-MM-DD"
        })
        return output.getvalue()

    @staticmethod
    async def allocate_to_facility(db: AsyncSession, ambulance_id: int, facility_id: int) -> Ambulance:
        ambulance = await AmbulanceService.get_by_id(db, ambulance_id)
        if not ambulance:
            raise ValueError("Ambulance not found")
        
        # Verify facility exists
        stmt = select(Facility).where(Facility.id == facility_id)
        res = await db.execute(stmt)
        if not res.scalars().first():
            raise ValueError("Facility not found")
            
        ambulance.facility_id = facility_id
        await db.commit()
        await db.refresh(ambulance)
        return ambulance

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):
        """Haversine formula to calculate distance between two points in km."""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    async def update_gps(
        db: AsyncSession, ambulance_id: int, obj_in: GPSHistoryCreate, state_id: Optional[int] = None
    ) -> Ambulance:
        ambulance = await AmbulanceService.get_by_id(db, ambulance_id=ambulance_id, state_id=state_id)
        if not ambulance:
            return None
        
        delta = 0.0
        if ambulance.last_latitude and ambulance.last_longitude:
            delta = AmbulanceService._calculate_distance(
                ambulance.last_latitude, ambulance.last_longitude,
                obj_in.latitude, obj_in.longitude
            )
        
        ambulance.last_latitude = obj_in.latitude
        ambulance.last_longitude = obj_in.longitude
        
        history = GPSHistory(
            ambulance_id=ambulance_id,
            incident_id=obj_in.incident_id,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            is_paused=obj_in.is_paused,
            incident_leg=obj_in.incident_leg,
            delta_distance=delta
        )
        db.add(history)
        
        if obj_in.incident_id:
            stmt = select(Dispatch).where(
                Dispatch.incident_id == obj_in.incident_id,
                Dispatch.ambulance_id == ambulance_id,
                Dispatch.completed_timestamp == None
            )
            result = await db.execute(stmt)
            dispatch = result.scalars().first()
            if dispatch:
                dispatch.total_distance += delta

        await db.commit()
        await db.refresh(ambulance)
        return ambulance

    @staticmethod
    async def update_status(
        db: AsyncSession, db_obj: Ambulance, new_status: AmbulanceStatus
    ) -> Ambulance:
        db_obj.status = new_status
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

ambulance_service = AmbulanceService()
