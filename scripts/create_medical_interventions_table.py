import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import engine
from app.models.medical_intervention import MedicalIntervention
from app.models.base import Base

async def create_medical_interventions_table():
    print("⏳ Creating medical_interventions table...")
    async with engine.begin() as conn:
        # We need to make sure the table is in the metadata
        await conn.run_sync(Base.metadata.create_all, tables=[MedicalIntervention.__table__])
    print("✅ Medical_interventions table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_medical_interventions_table())
