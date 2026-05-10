import asyncio
import json
import os
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.lga import LGA

async def seed_lgas():
    json_path = os.path.join(os.path.dirname(__file__), "lgas.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping LGAs: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        lgas_data = json.load(f)

    async with SessionLocal() as session:
        print(f"Seeding {len(lgas_data)} LGAs...")
        
        # Batch insert for efficiency
        stmt = insert(LGA).values([
            {
                "id": item["id"],
                "name": item["name"],
                "code": item.get("code", ""),
                "state_id": item.get("stateId") or item.get("state_id")
            }
            for item in lgas_data
        ]).on_conflict_do_nothing(index_elements=['id'])
        
        await session.execute(stmt)
        await session.commit()
        print("LGA Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_lgas())
