import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as session:
        await session.execute(text("UPDATE monitoring SET als = 0 WHERE als IS NULL"))
        await session.execute(text("UPDATE monitoring SET helicopters = 0 WHERE helicopters IS NULL"))
        await session.execute(text("UPDATE monitoring SET community_volunteers = 0 WHERE community_volunteers IS NULL"))
        await session.commit()
        print("Updated existing records to 0")

if __name__ == "__main__":
    asyncio.run(main())
