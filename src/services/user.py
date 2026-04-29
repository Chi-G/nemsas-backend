from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from src.db.models.user import User, Role
from src.db.models.auth import UserToken
from src.schemas.user import UserCreate, UserUpdate
from src.core.security import get_password_hash, verify_password
from typing import Optional, List

class UserService:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.phone_number == phone))
        return result.scalars().first()

    @staticmethod
    async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        result = await db.execute(select(Role).where(Role.name == name))
        return result.scalars().first()
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
    async def get_or_create_public_user(db: AsyncSession, phone: str, name: str = "Public Citizen") -> User:
        user = await UserService.get_by_phone(db, phone)
        if user:
            return user
            
        from src.core.rbac import RoleName
        role = await UserService.get_role_by_name(db, RoleName.CITIZEN)
        if not role:
            # Fallback if roles not seeded properly or in tests
            role_obj = Role(name=RoleName.CITIZEN, description="Public reporter via USSD/SMS")
            db.add(role_obj)
            await db.flush()
            role_id = role_obj.id
        else:
            role_id = role.id

        db_obj = User(
            email=f"{phone}@nemsas.gov.ng",
            phone_number=phone,
            name=name,
            hashed_password="!!!AUTHENTICATED_VIA_PHONE!!!",
            role_id=role_id,
            is_active=True,
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
        provider_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        query = select(User)
        if role_id:
            query = query.where(User.role_id == role_id)
        if state_id:
            query = query.where(User.state_id == state_id)
        if provider_id:
            query = query.where(User.provider_id == provider_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def count(
        db: AsyncSession, 
        role_id: Optional[int] = None, 
        state_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        query = select(func.count(User.id))
        if role_id:
            query = query.where(User.role_id == role_id)
        if state_id:
            query = query.where(User.state_id == state_id)
        if provider_id:
            query = query.where(User.provider_id == provider_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        result = await db.execute(query)
        return result.scalar() or 0

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
        # Invalidate existing activation/reset tokens for security (Criterion 51)
        await db.execute(
            update(UserToken)
            .where(UserToken.user_id == db_obj.id)
            .values(is_used=True)
        )
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def reactivate(db: AsyncSession, db_obj: User) -> User:
        db_obj.is_active = True
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    @staticmethod
    async def create_activation_token(db: AsyncSession, user_id: int) -> str:
        from src.services.auth import auth_service
        from src.db.models.auth import TokenType
        
        # 48 hours = 2880 minutes
        token_obj = await auth_service.create_token(
            db, user_id=user_id, token_type=TokenType.ACTIVATION, expires_in_minutes=2880
        )
        return token_obj.token

user_service = UserService()
