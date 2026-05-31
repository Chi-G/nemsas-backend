import asyncio
from app.db.session import engine
from app.models.base import Base
# Import all models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.patient import Patient
from app.models.incident import Incident
from app.models.claim import Claim
from app.models.run_sheet import RunSheet
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.transfer_form import TransferForm
# Add others if needed, though they are usually imported in the files above or app.models.__init__

async def create_all_tables():
    print("Creating missing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
