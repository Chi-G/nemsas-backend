from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.claim import Claim, ClaimStatus, ClaimType, ETCIntake
from src.db.models.run_sheet import RunSheet
from src.schemas.run_sheet import RunSheetUpdate
from src.schemas.claim import ClaimCreate, ETCIntakeCreate
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
            # We don't have dispatch_id here, but in theory we should. 
            # For backward compatibility, we'll try to find a dispatch or allow NULL if the model allowed it.
            # But the model requires it. Let's assume we can find it.
            from src.db.models.ambulance import Dispatch
            stmt = select(Dispatch).where(Dispatch.incident_id == incident_id)
            res = await db.execute(stmt)
            dispatch = res.scalars().first()
            if not dispatch:
                raise Exception("Cannot create run sheet without a dispatch assignment")
                
            run_sheet = RunSheet(incident_id=incident_id, dispatch_id=dispatch.id)
            db.add(run_sheet)
        
        from src.db.models.run_sheet import RunSheetStatus
        if run_sheet.status != RunSheetStatus.DRAFT:
            raise Exception("Run sheet is locked and cannot be edited")
            
        # Map fields from new schema
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(run_sheet, field):
                setattr(run_sheet, field, value)

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
