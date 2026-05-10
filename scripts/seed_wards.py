import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models.ward import Ward
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert

# Example data structure expected:
# {
#     "id": 1115,
#     "name": "Umuobasi",
#     "code": "",
#     "lgaId": 54,
#     "dateAdded": "2023-07-05T07:27:52+00:00"
# }

BATCH_SIZE = 1000

async def seed_wards_from_file(file_path: str):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    await seed_wards(data)

async def seed_wards(wards_data: list):
    async with SessionLocal() as session:
        total = len(wards_data)
        print(f"Starting seeding of {total} wards in batches of {BATCH_SIZE}...")
        
        for i in range(0, total, BATCH_SIZE):
            batch = wards_data[i:i + BATCH_SIZE]
            
            # Prepare batch for insert
            # We use Postgres 'insert ... on conflict do nothing' for efficiency
            stmt = insert(Ward).values([
                {
                    "id": item["id"],
                    "name": item["name"],
                    "code": item.get("code", ""),
                    "lga_id": item.get("lgaId") or item.get("lga_id"),
                    "date_added": datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00")) if "dateAdded" in item and item["dateAdded"] else datetime.now()
                }
                for item in batch
            ]).on_conflict_do_nothing(index_elements=['id'])
            
            await session.execute(stmt)
            await session.commit()
            
            print(f"Processed {min(i + BATCH_SIZE, total)} / {total}")

        print("Ward Seeding completed successfully.")

if __name__ == "__main__":
    # You can call this with a list or a path to a json file
    # Example: asyncio.run(seed_wards_from_file("wards.json"))
    print("Please use seed_wards(data) or seed_wards_from_file(path) in your script.")
