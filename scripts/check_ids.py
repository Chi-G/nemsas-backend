import asyncio
import sys
import os
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
import app.models.base  # Load registry
from sqlalchemy import select
from app.models.ambulance import Ambulance
from app.models.user import User

async def check():
    async with SessionLocal() as s:
        amb = await s.get(Ambulance, 204)
        usr = await s.get(User, "c7459df1-7a76-4fc8-a32a-9d6156bbe413")
        print(f"Ambulance 204: {amb is not None}")
        print(f"User c745...: {usr is not None}")

if __name__ == "__main__":
    asyncio.run(check())
