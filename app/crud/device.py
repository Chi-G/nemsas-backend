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
        from app.models.user import User as UserModel
        
        # Get users directly assigned to this ambulance
        user_select = select(UserModel.id).filter(UserModel.ambulance_id == ambulance_id)
        user_ids_result = await db.execute(user_select)
        user_ids = user_ids_result.scalars().all()
        
        if user_ids:
            query = select(Device).filter(
                (Device.ambulance_id == ambulance_id) | (Device.user_id.in_(user_ids))
            )
        else:
            query = select(Device).filter(Device.ambulance_id == ambulance_id)
            
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: DeviceCreate, user_id: UUID) -> Device:
        # Check if device already exists by push_token (since push_token is unique)
        db_obj = await self.get_by_token(db, push_token=obj_in.push_token)
        if db_obj:
            # Update fields
            db_obj.user_id = user_id
            db_obj.device_id = obj_in.device_id
            db_obj.ambulance_id = obj_in.ambulance_id
            db_obj.platform = obj_in.platform
            db_obj.device_name = obj_in.device_name
            await db.commit()
            await db.refresh(db_obj)
            return db_obj

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
