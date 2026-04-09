from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.claim import Claim, RunSheet, ClaimStatus, ClaimType, ETCIntake
from src.schemas.claim import ClaimCreate, RunSheetUpdate, ETCIntakeCreate
from datetime import datetime, timezone
from typing import List, Optional, Any

class ClaimService:
    @staticmethod
    async def get_run_sheet(db: AsyncSession, incident_id: int, state_id: Optional[int] = None) -> Optional[RunSheet]:
        from src.db.models.incident import Incident
        stmt = select(RunSheet).where(RunSheet.incident_id == incident_id)
        if state_id:
            stmt = stmt.join(Incident).where(Incident.state_id == state_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_or_update_run_sheet(
        db: AsyncSession, incident_id: int, obj_in: RunSheetUpdate, user_id: int, state_id: Optional[int] = None
    ) -> RunSheet:
        from src.db.models.incident import Incident
        incident = await db.get(Incident, incident_id)
        if not incident:
            raise Exception("Incident not found")
        
        if state_id and incident.state_id != state_id:
            raise Exception("Access denied: Incident belongs to another state")

        run_sheet = await ClaimService.get_run_sheet(db, incident_id=incident_id)
        if not run_sheet:
            run_sheet = RunSheet(incident_id=incident_id)
            db.add(run_sheet)
        
        if run_sheet.is_locked:
            raise Exception("Run sheet is locked and cannot be edited")
            
        if obj_in.patient_data is not None:
            run_sheet.patient_data = obj_in.patient_data
        if obj_in.drugs_administered is not None:
            run_sheet.drugs_administered = obj_in.drugs_administered
            
        if obj_in.crew_signature:
            run_sheet.crew_signature = obj_in.crew_signature
            run_sheet.crew_signed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run_sheet.crew_id = user_id
            
        if obj_in.etc_signature:
            run_sheet.etc_signature = obj_in.etc_signature
            run_sheet.etc_signed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run_sheet.etc_staff_id = user_id
            run_sheet.is_locked = True # Lock after both signatures (simplified)

        await db.commit()
        await db.refresh(run_sheet)
        return run_sheet

    @staticmethod
    async def create_claim(
        db: AsyncSession, incident_id: int, user_id: int, claim_type: ClaimType, amount: float, distance_km: float = None
    ) -> Claim:
        db_obj = Claim(
            incident_id=incident_id,
            user_id=user_id,
            claim_type=claim_type,
            amount=amount,
            distance_km=distance_km,
            status=ClaimStatus.PENDING,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def process_claim(
        db: AsyncSession, claim_id: int, status: ClaimStatus, processor_id: int, state_id: Optional[int] = None, reason: str = None
    ) -> Optional[Claim]:
        from src.db.models.incident import Incident
        stmt = select(Claim).where(Claim.id == claim_id)
        if state_id:
            stmt = stmt.join(Incident).where(Incident.state_id == state_id)
        
        result = await db.execute(stmt)
        claim = result.scalars().first()
        if not claim:
            return None
            
        claim.status = status
        claim.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        claim.processed_by_id = processor_id
        claim.rejection_reason = reason
        
        await db.commit()
        await db.refresh(claim)
        return claim

claim_service = ClaimService()
