import asyncio
import json
import os
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.role import Role

async def seed_roles():
    json_path = os.path.join(os.path.dirname(__file__), "roles.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Roles: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        roles_data = json.load(f)

    async with SessionLocal() as session:
        print(f"Seeding {len(roles_data)} roles...")
        
        stmt = insert(Role).values([
            {"id": item["id"], "name": item["name"]}
            for item in roles_data
        ]).on_conflict_do_nothing(index_elements=['id'])
        
        await session.execute(stmt)
        await session.commit()
        print("Role Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_roles())
