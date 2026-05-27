from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from typing import List, Optional, Tuple
from app.models.transfer_form import TransferForm
from app.schemas.transfer_form import TransferFormBindingModel, TransferFormUpdateBindingModel

class CRUDTransferForm:
    async def get(self, db: AsyncSession, id: int) -> Optional[TransferForm]:
        stmt = select(TransferForm).where(TransferForm.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        incident_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        etc_id: Optional[int] = None,
        run_sheet_id: Optional[int] = None
    ) -> Tuple[List[TransferForm], int]:
        stmt = select(TransferForm).order_by(desc(TransferForm.id))
        count_stmt = select(func.count()).select_from(TransferForm)
        
        base_filters = []
        if incident_id is not None:
            base_filters.append(TransferForm.incident_id == incident_id)
        if patient_id is not None:
            base_filters.append(TransferForm.patient_id == patient_id)
        if etc_id is not None:
            base_filters.append(TransferForm.etc_id == etc_id)
        if run_sheet_id is not None:
            base_filters.append(TransferForm.run_sheet_id == run_sheet_id)

        if base_filters:
            stmt = stmt.where(*base_filters)
            count_stmt = count_stmt.where(*base_filters)
            
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

    async def create(self, db: AsyncSession, *, obj_in: TransferFormBindingModel) -> TransferForm:
        db_obj = TransferForm(
            incident_id=obj_in.incident_id,
            medic_user_id=obj_in.medic_user_id,
            hospice_user_id=obj_in.hospice_user_id,
            patient_id=obj_in.patient_id,
            patient_ids=obj_in.patient_ids,
            etc_id=obj_in.etc_id,
            run_sheet_id=obj_in.run_sheet_id,
            approve=obj_in.approve
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Real-time Broadcast via Socket.IO
        try:
            from app.models.incident import Incident
            from app.core.socket_manager import SocketManager
            stmt = select(Incident.state_id).where(Incident.id == db_obj.incident_id)
            state_id = await db.scalar(stmt)
            if state_id:
                await SocketManager.broadcast_incident_update(
                    state_id,
                    {
                        "type": "NEW_TRANSFER_FORM",
                        "transferFormId": db_obj.id,
                        "incidentId": db_obj.incident_id,
                        "patientId": db_obj.patient_id,
                        "patientIds": db_obj.patient_ids,
                        "etcId": db_obj.etc_id,
                        "runSheetId": db_obj.run_sheet_id,
                        "approve": db_obj.approve
                    }
                )
        except Exception as e:
            # Prevent failures in websocket broadcasting from breaking the main db transaction
            import logging
            logging.getLogger(__name__).error(f"Failed to broadcast websocket update: {e}")

        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: TransferForm, 
        obj_in: TransferFormUpdateBindingModel
    ) -> TransferForm:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Real-time Broadcast via Socket.IO
        try:
            from app.models.incident import Incident
            from app.core.socket_manager import SocketManager
            stmt = select(Incident.state_id).where(Incident.id == db_obj.incident_id)
            state_id = await db.scalar(stmt)
            if state_id:
                await SocketManager.broadcast_incident_update(
                    state_id,
                    {
                        "type": "TRANSFER_FORM_UPDATE",
                        "transferFormId": db_obj.id,
                        "incidentId": db_obj.incident_id,
                        "patientId": db_obj.patient_id,
                        "patientIds": db_obj.patient_ids,
                        "etcId": db_obj.etc_id,
                        "runSheetId": db_obj.run_sheet_id,
                        "approve": db_obj.approve
                    }
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to broadcast websocket update: {e}")

        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[TransferForm]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

transfer_form = CRUDTransferForm()
