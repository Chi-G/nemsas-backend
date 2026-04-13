from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status

from src.db.models.incident import Incident, IncidentStatus
from src.db.models.claim import ETCIntake, Claim, ClaimType, ClaimStatus
from src.db.models.run_sheet import RunSheet, RunSheetStatus
from src.schemas.etc import ETCIntakeCreate, ETCClaimCreate

class ETCService:
    @staticmethod
    async def get_incoming_patients(db: AsyncSession, facility_id: int) -> List[Incident]:
        """
        Criterion 114: List active incidents assigned to this ETC facility.
        Include PATIENT_LOADED (expected), EN_ROUTE_TO_ETC (en route), and ARRIVED_AT_ETC (just arrived).
        """
        stmt = select(Incident).where(
            and_(
                Incident.destination_facility_id == facility_id,
                Incident.status.in_([
                    IncidentStatus.PATIENT_LOADED,
                    IncidentStatus.EN_ROUTE_TO_ETC,
                    IncidentStatus.ARRIVED_AT_ETC
                ])
            )
        ).options(selectinload(Incident.status_history)).order_by(Incident.created_at.desc())
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_intake(db: AsyncSession, intake_in: ETCIntakeCreate, facility_id: int) -> ETCIntake:
        """
        Criterion 110-112: Record patient arrival and initial triage.
        """
        # Verify incident exists
        incident = await db.get(Incident, intake_in.incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
            
        # Check if intake already exists
        existing_stmt = select(ETCIntake).where(ETCIntake.incident_id == intake_in.incident_id)
        existing = await db.execute(existing_stmt)
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Intake record already exists for this incident")

        db_intake = ETCIntake(
            **intake_in.model_dump(),
            etc_facility_id=facility_id
        )
        
        # Automatically update incident status to ARRIVED_AT_ETC if it isn't already
        if incident.status != IncidentStatus.ARRIVED_AT_ETC:
            incident.status = IncidentStatus.ARRIVED_AT_ETC
            
        db.add(db_intake)
        await db.commit()
        await db.refresh(db_intake)
        return db_intake

    @staticmethod
    async def cosign_run_sheet(db: AsyncSession, run_sheet_id: int, user_id: int) -> RunSheet:
        """
        Criterion 116-118: ETC staff co-signs the ambulance run sheet.
        """
        stmt = select(RunSheet).where(RunSheet.id == run_sheet_id).options(selectinload(RunSheet.drug_entries))
        result = await db.execute(stmt)
        run_sheet = result.scalars().first()
        if not run_sheet:
            raise HTTPException(status_code=404, detail="Run sheet not found")
            
        # Criterion 117: Check status is correct
        if run_sheet.status != RunSheetStatus.CREW_SIGNED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Run sheet is not in a state awaiting ETC co-signature"
            )
            
        # Update status and record signature
        run_sheet.status = RunSheetStatus.FULLY_SIGNED
        run_sheet.etc_signature_id = user_id
        run_sheet.etc_signed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await db.commit()
        await db.refresh(run_sheet)
        return run_sheet

    @staticmethod
    async def create_hospital_claim(db: AsyncSession, claim_in: ETCClaimCreate, user_id: int) -> Claim:
        """
        Criterion 119-122: Hospital submits their own claim for the incident.
        """
        # Check if claim already exists for this incident/user/type
        stmt = select(Claim).where(
            and_(
                Claim.incident_id == claim_in.incident_id,
                Claim.user_id == user_id,
                Claim.claim_type == ClaimType.ETC
            )
        )
        existing = await db.execute(stmt)
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Claim already submitted for this incident")
            
        db_claim = Claim(
            incident_id=claim_in.incident_id,
            user_id=user_id,
            claim_type=ClaimType.ETC,
            amount=claim_in.amount,
            status=ClaimStatus.PENDING
        )
        
        db.add(db_claim)
        await db.commit()
        await db.refresh(db_claim)
        return db_claim
