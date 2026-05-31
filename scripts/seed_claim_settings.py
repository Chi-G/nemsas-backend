import asyncio
from datetime import datetime
from app.db.session import SessionLocal
from app.models.claim_setting import ClaimSetting
from sqlalchemy.future import select

async def seed_claim_settings():
    async with SessionLocal() as db:
        # Check if exists
        existing = await db.execute(select(ClaimSetting).where(ClaimSetting.key == "ETCClaimExpirationInHours"))
        if existing.scalars().first():
            print("Already seeded")
            return
            
        new_setting = ClaimSetting(
            id=2,
            key="ETCClaimExpirationInHours",
            value="48",
            date_updated=datetime.fromisoformat("2026-01-25T08:48:03.207621+00:00")
        )
        db.add(new_setting)
        await db.commit()
        print("Claim settings seeded successfully")

if __name__ == "__main__":
    asyncio.run(seed_claim_settings())
