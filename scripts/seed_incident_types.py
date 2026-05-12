import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.incident_type import IncidentType

async def seed_incident_types():
    json_path = os.path.join(os.path.dirname(__file__), "incident_type.json")

    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Incident Types: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        print(f"🏷️  Seeding {len(data)} Incident Types...")

        for item in data:
            date_added = None
            if item.get("dateAdded"):
                try:
                    date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                except Exception:
                    date_added = datetime.now()

            stmt = insert(IncidentType).values(
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
        print("✅ Incident Types seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_incident_types())
