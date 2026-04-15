from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.claim import Claim, ClaimStatus, ClaimType, ETCIntake, ClaimAuditLog, ClaimAction
from src.db.models.run_sheet import RunSheet, RunSheetDrugEntry, RunSheetStatus
from src.db.models.incident import Incident
from src.db.models.ambulance import Dispatch, Ambulance
from src.schemas.run_sheet import RunSheetUpdate
from src.schemas.claim import ClaimCreate, ETCIntakeCreate, ClaimFilter, ClaimPair, ClaimDetail
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
import csv
import io

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
    async def get_claims_paginated(
        db: AsyncSession, 
        filters: ClaimFilter, 
        skip: int = 0, 
        limit: int = 100,
        state_id: Optional[int] = None
    ) -> List[ClaimPair]:
        stmt = select(Incident).order_by(Incident.created_at.desc())
        
        # Filtering logic
        if state_id:
            stmt = stmt.where(Incident.state_id == state_id)
        elif filters.state_id:
            stmt = stmt.where(Incident.state_id == filters.state_id)
            
        if filters.lga_id:
            stmt = stmt.where(Incident.lga_id == filters.lga_id)
        
        # Join with claims for filtering by claim status/type if needed
        # But requirements say "Claims are returned in pairs ... for the same incident"
        # So we filter incidents that have at least one claim, or simply return all incidents that match filters and then fetch their claims.
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        incidents = result.scalars().all()
        
        pairs = []
        for incident in incidents:
            # Fetch claims for this incident
            claim_stmt = select(Claim).where(Claim.incident_id == incident.id)
            if filters.claim_type:
                claim_stmt = claim_stmt.where(Claim.claim_type == filters.claim_type)
            if filters.status:
                claim_stmt = claim_stmt.where(Claim.status == filters.status)
            
            c_res = await db.execute(claim_stmt)
            claims = c_res.scalars().all()
            
            if not claims and (filters.status or filters.claim_type):
                continue # Skip if filtered out
                
            amb_claim = next((c for c in claims if c.claim_type == ClaimType.AMBULANCE), None)
            etc_claim = next((c for c in claims if c.claim_type == ClaimType.ETC), None)
            
            # If no claims but filters didn't exclude them, we might still want to see the incident row?
            # Usually for a "Claims Queue", we only want incidents with at least one claim.
            if not amb_claim and not etc_claim:
                continue

            pairs.append(ClaimPair(
                incident_id=incident.id,
                incident_uuid=incident.uuid,
                ambulance_claim=amb_claim,
                etc_claim=etc_claim
            ))
            
        return pairs

    @staticmethod
    async def get_claim_detail(db: AsyncSession, claim_id: int, state_id: Optional[int] = None) -> Optional[ClaimDetail]:
        stmt = select(Claim).where(Claim.id == claim_id)
        if state_id:
            stmt = stmt.join(Incident).where(Incident.state_id == state_id)
        
        result = await db.execute(stmt)
        claim = result.scalars().first()
        if not claim:
            return None
            
        incident = await db.get(Incident, claim.incident_id)
        run_sheet = await ClaimService.get_run_sheet(db, incident.id)
        
        # Get ambulance info from dispatch
        dispatch_stmt = select(Dispatch).where(Dispatch.incident_id == incident.id)
        d_res = await db.execute(dispatch_stmt)
        dispatch = d_res.scalars().first()
        
        ambulance_plate = None
        ambulance_type = None
        if dispatch:
            amb = await db.get(Ambulance, dispatch.ambulance_id)
            if amb:
                ambulance_plate = amb.plate_number
                ambulance_type = amb.accreditation_type.value
        
        drug_list = []
        if run_sheet:
            from sqlalchemy.orm import selectinload
            rs_stmt = select(RunSheet).where(RunSheet.id == run_sheet.id).options(selectinload(RunSheet.drug_entries))
            rs_res = await db.execute(rs_stmt)
            run_sheet_full = rs_res.scalars().first()
            if run_sheet_full:
                 drug_list = [d.custom_drug_name or f"Drug #{d.drug_id}" for d in run_sheet_full.drug_entries]

        # Fee calculation logic metadata
        calc_logic = "BLS: Fixed NGN 15,000" if ambulance_type == "BLS" else "ALS: Variable (NGN 20,000 + distance allowance)"
        
        return ClaimDetail(
            **Claim.model_validate(claim).model_dump(),
            incident_uuid=incident.uuid,
            ambulance_plate=ambulance_plate,
            ambulance_type=ambulance_type,
            run_sheet_status=run_sheet.status.value if run_sheet else None,
            is_fully_signed=(run_sheet.status == RunSheetStatus.FULLY_SIGNED) if run_sheet else False,
            patient_name=run_sheet.patient_name if run_sheet else None,
            drug_list=drug_list,
            calculation_logic=calc_logic
        )

    @staticmethod
    def calculate_fee(ambulance_type: str, distance_km: float = 0.0) -> float:
        if ambulance_type == "BLS":
            return 15000.0
        else:
            # ALS: Base 20,000 + 500 per km
            return 20000.0 + (distance_km * 500.0)

    @staticmethod
    async def process_claim(
        db: AsyncSession, claim_id: int, status: ClaimStatus, processor_id: int, state_id: Optional[int] = None, reason: str = None
    ) -> Optional[Claim]:
        stmt = select(Claim).where(Claim.id == claim_id)
        if state_id:
            stmt = stmt.join(Incident).where(Incident.state_id == state_id)
        
        result = await db.execute(stmt)
        claim = result.scalars().first()
        if not claim:
            return None
            
        if status == ClaimStatus.REJECTED and not reason:
            raise Exception("Rejection reason is mandatory")
            
        claim.status = status
        claim.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        claim.processed_by_id = processor_id
        claim.rejection_reason = reason
        
        # Add Audit Log
        audit = ClaimAuditLog(
            claim_id=claim.id,
            action=ClaimAction.APPROVE if status == ClaimStatus.APPROVED else ClaimAction.REJECT,
            processed_by_id=processor_id,
            rejection_reason=reason
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(claim)
        
        # Notify
        from src.services.notification import notification_service
        await notification_service.send_claim_status_notification(claim.user_id, claim.id, status.value)
        
        return claim

    @staticmethod
    async def export_claims_csv(db: AsyncSession, filters: ClaimFilter, state_id: Optional[int] = None) -> str:
        pairs = await ClaimService.get_claims_paginated(db, filters, limit=1000, state_id=state_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Incident UUID", "Ambulance Claim ID", "Ambulance Amount", "Ambulance Status", "ETC Claim ID", "ETC Amount", "ETC Status"])
        
        for p in pairs:
            writer.writerow([
                p.incident_uuid,
                p.ambulance_claim.id if p.ambulance_claim else "N/A",
                p.ambulance_claim.amount if p.ambulance_claim else 0,
                p.ambulance_claim.status if p.ambulance_claim else "N/A",
                p.etc_claim.id if p.etc_claim else "N/A",
                p.etc_claim.amount if p.etc_claim else 0,
                p.etc_claim.status if p.etc_claim else "N/A",
            ])
            
        return output.getvalue()

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

claim_service = ClaimService()
