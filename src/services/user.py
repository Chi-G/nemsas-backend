from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.user import User, Role
from src.schemas.user import UserCreate, UserUpdate
from src.core.security import get_password_hash, verify_password
from typing import Optional, List

class UserService:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await UserService.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def create(db: AsyncSession, obj_in: UserCreate, password: str) -> User:
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            hashed_password=get_password_hash(password),
            role_id=obj_in.role_id,
            provider_id=obj_in.provider_id,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def list(
        db: AsyncSession, 
        role_id: Optional[int] = None, 
        state_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        query = select(User)
        if role_id:
            query = query.where(User.role_id == role_id)
        if state_id:
            query = query.where(User.state_id == state_id)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def deactivate(db: AsyncSession, db_obj: User) -> User:
        db_obj.is_active = False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

user_service = UserService()
