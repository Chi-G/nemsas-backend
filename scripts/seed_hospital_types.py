import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.hospital_type import HospitalType

async def seed_hospital_types():
    json_path = os.path.join(os.path.dirname(__file__), "hospital_types.json")
    
    # Fallback data if JSON doesn't exist yet
    default_data = [
        {
            "id": 3,
            "name": "Private",
            "description": "Private",
            "dateAdded": "2026-01-07T17:54:12.887767+00:00"
        },
        {
            "id": 2,
            "name": "Tertiary",
            "description": "Tertiary",
            "dateAdded": "2026-01-07T17:54:12.887767+00:00"
        },
        {
            "id": 1,
            "name": "General",
            "description": "General",
            "dateAdded": "2026-02-26T19:43:59.19848+00:00"
        }
    ]

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
    else:
        data = default_data
        # Save the default data to JSON for future use
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

    async with SessionLocal() as session:
        print(f"🏥 Seeding {len(data)} Hospital Types...")
        
        for item in data:
            # Parse date
            date_added = None
            if item.get("dateAdded"):
                try:
                    date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                except:
                    date_added = datetime.now()

            stmt = insert(HospitalType).values(
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
        print("✅ Hospital Types seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_hospital_types())
