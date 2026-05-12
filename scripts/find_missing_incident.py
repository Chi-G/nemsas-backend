import asyncio
import json
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.incident import Incident
from sqlalchemy import select

async def find_missing_incident():
    with open('scripts/incidentsNew.json', 'r') as f:
        data = json.load(f)
    
    json_ids = {item.get("id") for item in data if isinstance(item, dict)}
    print(f"Total IDs in JSON: {len(json_ids)}")

    async with SessionLocal() as session:
        result = await session.execute(select(Incident.id))
        db_ids = set(result.scalars().all())
        print(f"Total IDs in DB: {len(db_ids)}")

        missing = json_ids - db_ids
        print(f"Missing IDs: {missing}")
        
        # Check if there's any duplicate ID in JSON
        if len(json_ids) < len(data):
            print(f"Duplicate IDs in JSON: {len(data) - len(json_ids)}")

if __name__ == "__main__":
    asyncio.run(find_missing_incident())
