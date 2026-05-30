import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, Base
from app.models.claim import Claim
from app.models.etc_intervention import EtcIntervention

async def recreate_tables():
    print("Recreating missing tables...")
    async with engine.begin() as conn:
        # Create all tables that are registered with the Base
        await conn.run_sync(Base.metadata.create_all)
    print("Missing tables created successfully!")

if __name__ == "__main__":
    asyncio.run(recreate_tables())
