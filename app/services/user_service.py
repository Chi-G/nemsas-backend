from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import user_crud
from app.schemas.user import UserCreate

class UserService:
    async def register_user(self, db: AsyncSession, user_in: UserCreate):
        # Add business logic here (e.g. sending welcome email, etc.)
        return await user_crud.create(db, obj_in=user_in)

user_service = UserService()
