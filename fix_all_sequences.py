import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text

TABLES = [
    "claims",
    "claim_images",
    "incidents",
    "patients",
    "medical_interventions",
    "etc_interventions",
    "run_sheets",
    "etc_intakes",
    "ambulances",
    "hospitals",
    "lgas",
    "states"
]

async def main():
    async with SessionLocal() as session:
        for table in TABLES:
            try:
                seq_name = f"{table}_id_seq"
                await session.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table}), 1));"))
                await session.commit()
                print(f"Successfully updated {seq_name}")
            except Exception as e:
                # rollback to prevent InFailedSQLTransactionError for subsequent queries
                await session.rollback()
                print(f"Error updating {seq_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
