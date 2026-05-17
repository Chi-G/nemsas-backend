from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
from uuid import UUID
from typing import List, Optional

class CRUDDevice:
    async def get(self, db: AsyncSession, id: UUID) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.id == id))
        return result.scalars().first()

    async def get_by_token(self, db: AsyncSession, push_token: str) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.push_token == push_token))
        return result.scalars().first()

    async def get_by_device_id(self, db: AsyncSession, user_id: UUID, device_id: str) -> Optional[Device]:
        result = await db.execute(
            select(Device).filter(Device.user_id == user_id, Device.device_id == device_id)
        )
        return result.scalars().first()

    async def get_multi_by_user(self, db: AsyncSession, user_id: UUID) -> List[Device]:
        result = await db.execute(select(Device).filter(Device.user_id == user_id))
        return result.scalars().all()

    async def get_multi_by_ambulance(self, db: AsyncSession, ambulance_id: int) -> List[Device]:
        result = await db.execute(select(Device).filter(Device.ambulance_id == ambulance_id))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: DeviceCreate, user_id: UUID) -> Device:
        # Check if device already exists for this user by device_id
        if obj_in.device_id:
            db_obj = await self.get_by_device_id(db, user_id=user_id, device_id=obj_in.device_id)
            if db_obj:
                # Update token if changed
                db_obj.push_token = obj_in.push_token
                db_obj.ambulance_id = obj_in.ambulance_id
                await db.commit()
                await db.refresh(db_obj)
                return db_obj

        # Otherwise create new
        db_obj = Device(
            **obj_in.model_dump(exclude_none=True),
            user_id=user_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: UUID) -> Device:
        result = await db.execute(select(Device).filter(Device.id == id))
        obj = result.scalars().first()
        await db.delete(obj)
        await db.commit()
        return obj

device_crud = CRUDDevice()
