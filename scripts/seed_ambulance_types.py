import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.ambulance_type import AmbulanceType

async def seed_ambulance_types():
    json_path = os.path.join(os.path.dirname(__file__), "ambulance_types.json")
    
    # Data from user request
    default_data = [
        {
            "id": 1,
            "name": "BLS",
            "description": "BLS",
            "dateAdded": "2026-02-26T19:43:59.198507+00:00"
        },
        {
            "id": 2,
            "name": "ALS",
            "description": "ALS",
            "dateAdded": "2026-02-26T19:43:59.198507+00:00"
        },
        {
            "id": 3,
            "name": "Keke",
            "description": "Keke",
            "dateAdded": "2026-02-26T19:43:59.198507+00:00"
        },
        {
            "id": 4,
            "name": "Boat",
            "description": "Boat",
            "dateAdded": "2026-02-26T19:43:59.198508+00:00"
        }
    ]

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
    else:
        data = default_data
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

    async with SessionLocal() as session:
        print(f"🚑 Seeding {len(data)} Ambulance Types...")
        
        for item in data:
            date_added = None
            if item.get("dateAdded"):
                try:
                    date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                except:
                    date_added = datetime.now()

            stmt = insert(AmbulanceType).values(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                date_added=date_added
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'name': item['name'],
                    'description': item.get('description'),
                    'date_added': date_added
                }
            )
            await session.execute(stmt)
        
        await session.commit()
        print("✅ Ambulance Types seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_ambulance_types())
