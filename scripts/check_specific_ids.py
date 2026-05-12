import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from sqlalchemy import select

async def check_ids():
    async with SessionLocal() as session:
        # Check for ambulance 115 and hospital 19
        amb = await session.scalar(select(Ambulance).where(Ambulance.id == 115))
        hosp = await session.scalar(select(Hospital).where(Hospital.id == 19))
        
        print(f"Ambulance 115: {'FOUND' if amb else 'NOT FOUND'}")
        print(f"Hospital 19: {'FOUND' if hosp else 'NOT FOUND'}")

if __name__ == "__main__":
    asyncio.run(check_ids())
