import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import engine
from app.models.patient import Patient
from app.models.base import Base

async def create_patients_table():
    print("⏳ Creating patients table...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[Patient.__table__])
    print("✅ Patients table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_patients_table())
