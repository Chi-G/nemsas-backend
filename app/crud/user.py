from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Any
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class CRUDUser:
    async def get(self, db: AsyncSession, id: Any) -> Optional[User]:
        result = await db.execute(
            select(User)
            .filter(User.id == id)
            .options(selectinload(User.state), selectinload(User.lga), selectinload(User.ward))
        )
        return result.scalars().first()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .filter(User.email == email)
            .options(selectinload(User.state), selectinload(User.lga), selectinload(User.ward))
        )
        return result.scalars().first()

    
    async def get_by_username(self, db: AsyncSession, user_name: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .filter(User.user_name == user_name)
            .options(selectinload(User.state), selectinload(User.lga), selectinload(User.ward))
        )
        return result.scalars().first()


    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        from sqlalchemy import func, or_
        
        query = select(User)
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.middle_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get records
        result = await db.execute(
            query
            .order_by(User.date_joined.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(User.state), selectinload(User.lga), selectinload(User.ward))
        )
        return result.scalars().all(), total

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            first_name=obj_in.first_name,
            middle_name=obj_in.middle_name,
            last_name=obj_in.last_name,
            user_name=obj_in.user_name,
            email=obj_in.email,
            phone_number=obj_in.phone_number,
            hashed_password=get_password_hash(obj_in.password),
            sex=obj_in.sex,
            street1=obj_in.street1,
            street2=obj_in.street2,
            city=obj_in.city,
            user_type=obj_in.user_type,
            real_user_type=obj_in.real_user_type,
            organisation_name=obj_in.organisation_name,
            supervisor_user_id=obj_in.supervisor_user_id,
            emergency_treatment_center_id=obj_in.emergency_treatment_center_id,
            etc_id=obj_in.etc_id,
            ambulance_id=obj_in.ambulance_id,
            state_id=obj_in.state_id,
            lga_id=obj_in.lga_id,
            ward_id=obj_in.ward_id
        )
        db.add(db_obj)
        await db.commit()
        return await self.get(db, id=db_obj.id)


user_crud = CRUDUser()
