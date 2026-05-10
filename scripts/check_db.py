import asyncio
from sqlalchemy import func
from sqlalchemy.future import select
from app.db.session import SessionLocal
from app.models.user import User

async def check_db():
    async with SessionLocal() as session:
        # Check User Count
        count_result = await session.execute(select(func.count()).select_from(User))
        total = count_result.scalar()
        print(f"📊 Total Users in Database: {total}")
        
        if total > 0:
            # Show first 5 users
            users_result = await session.execute(select(User).limit(5))
            users = users_result.scalars().all()
            for u in users:
                print(f" - {u.email} (ID: {u.id})")

if __name__ == "__main__":
    asyncio.run(check_db())
