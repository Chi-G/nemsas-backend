from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.db.models.run_sheet import RunSheet, RunSheetDrugEntry, RunSheetHistory, RunSheetStatus
from src.db.models.reference import Drug
from src.schemas.run_sheet import RunSheetCreate, RunSheetUpdate
from datetime import datetime, timezone
from typing import List, Optional, Any
import json

class RunSheetService:
    @staticmethod
    async def create_initial_run_sheet(
        db: AsyncSession, obj_in: RunSheetCreate
    ) -> RunSheet:
        db_obj = RunSheet(
            incident_id=obj_in.incident_id,
            dispatch_id=obj_in.dispatch_id,
            status=RunSheetStatus.DRAFT
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, run_sheet_id: int) -> Optional[RunSheet]:
        stmt = select(RunSheet).where(RunSheet.id == run_sheet_id).options(selectinload(RunSheet.drug_entries))
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_incident_id(db: AsyncSession, incident_id: int) -> Optional[RunSheet]:
        stmt = select(RunSheet).where(RunSheet.incident_id == incident_id).options(selectinload(RunSheet.drug_entries))
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def progressive_save(
        db: AsyncSession, run_sheet_id: int, obj_in: RunSheetUpdate, user_id: int
    ) -> RunSheet:
        run_sheet = await RunSheetService.get_by_id(db, run_sheet_id)
        if not run_sheet:
            raise Exception("Run Sheet not found")
        
        if run_sheet.status != RunSheetStatus.DRAFT:
            raise Exception("Run Sheet is locked and cannot be edited")

        # Update basic fields
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"drug_entries"})
        for field, value in update_data.items():
            setattr(run_sheet, field, value)

        # Handle drug entries if provided
        if obj_in.drug_entries is not None:
            # For simplicity in this implementation, we clear and re-add 
            # In production, we might want to sync/update specific entries
            from sqlalchemy import delete
            await db.execute(delete(RunSheetDrugEntry).where(RunSheetDrugEntry.run_sheet_id == run_sheet_id))
            
            for drug_in in obj_in.drug_entries:
                is_nhia = True
                if drug_in.drug_id:
                    drug_ref = await db.get(Drug, drug_in.drug_id)
                    is_nhia = drug_ref.is_nhia_approved if drug_ref else False
                
                drug_entry = RunSheetDrugEntry(
                    run_sheet_id=run_sheet_id,
                    drug_id=drug_in.drug_id,
                    custom_drug_name=drug_in.custom_drug_name,
                    dosage=drug_in.dosage,
                    administered_at=drug_in.administered_at or datetime.now(timezone.utc).replace(tzinfo=None),
                    is_reimbursable=is_nhia
                )
                db.add(drug_entry)

        # Record history snapshot
        history = RunSheetHistory(
            run_sheet_id=run_sheet_id,
            data_snapshot=obj_in.model_dump(),
            saved_by_id=user_id
        )
        db.add(history)

        await db.commit()
        await db.refresh(run_sheet)
        return run_sheet

    @staticmethod
    async def sign_by_crew(db: AsyncSession, run_sheet_id: int, user_id: int) -> RunSheet:
        run_sheet = await RunSheetService.get_by_id(db, run_sheet_id)
        if not run_sheet:
            raise Exception("Run Sheet not found")
        
        if run_sheet.status != RunSheetStatus.DRAFT:
            raise Exception("Run Sheet is already signed or locked")

        run_sheet.status = RunSheetStatus.CREW_SIGNED
        run_sheet.crew_signature_id = user_id
        run_sheet.crew_signed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await db.commit()
        await db.refresh(run_sheet)
        return run_sheet

    @staticmethod
    async def get_drug_list(db: AsyncSession, query: Optional[str] = None) -> List[Drug]:
        stmt = select(Drug).where(Drug.is_active == True)
        if query:
            stmt = stmt.where(Drug.name.ilike(f"%{query}%"))
        result = await db.execute(stmt)
        return result.scalars().all()

run_sheet_service = RunSheetService()
