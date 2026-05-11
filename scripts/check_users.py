import asyncio
import sys
import os
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from sqlalchemy import select, func
from app.models.user import User
from app.models.hospital import Hospital
from app.models.ambulance import Ambulance
from app.models.state import State
from app.models.lga import LGA
from app.models.ward import Ward

async def check():
    async with SessionLocal() as s:
        u = await s.scalar(select(func.count()).select_from(User))
        h = await s.scalar(select(func.count()).select_from(Hospital))
        a = await s.scalar(select(func.count()).select_from(Ambulance))
        st = await s.scalar(select(func.count()).select_from(State))
        lg = await s.scalar(select(func.count()).select_from(LGA))
        wa = await s.scalar(select(func.count()).select_from(Ward))
        
        print(f"USERS: {u}")
        print(f"HOSPITALS: {h}")
        print(f"AMBULANCES: {a}")
        print(f"STATES: {st}")
        print(f"LGAS: {lg}")
        print(f"WARDS: {wa}")

if __name__ == "__main__":
    asyncio.run(check())
