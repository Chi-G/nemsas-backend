import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.patient import Patient
from sqlalchemy import func, select

async def check_counts():
    async with SessionLocal() as session:
        incident_count = await session.scalar(select(func.count()).select_from(Incident))
        ambulance_count = await session.scalar(select(func.count()).select_from(Ambulance))
        hospital_count = await session.scalar(select(func.count()).select_from(Hospital))
        patient_count = await session.scalar(select(func.count()).select_from(Patient))
        
        print(f"📊 Current Counts:")
        print(f" - Incidents: {incident_count}")
        print(f" - Patients: {patient_count}")
        print(f" - Ambulances: {ambulance_count}")
        print(f" - Hospitals: {hospital_count}")

if __name__ == "__main__":
    asyncio.run(check_counts())
