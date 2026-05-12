import asyncio
import json
import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.hospital import Hospital
from app.models.hospital_type import HospitalType
from app.models.state import State
from app.models.lga import LGA

async def seed_hospitals():
    json_path = "scripts/hospitals.json"
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        # Get all valid foreign keys to avoid violations
        type_ids = set((await session.execute(select(HospitalType.id))).scalars().all())
        state_ids = set((await session.execute(select(State.id))).scalars().all())
        lga_ids = set((await session.execute(select(LGA.id))).scalars().all())
        
        print(f"✅ Found {len(type_ids)} hospital types, {len(state_ids)} states, {len(lga_ids)} LGAs.")

        print(f"🏥 Preparing {len(data)} Hospitals...")
        
        to_insert = []
        for item in data:
            date_added = None
            if item.get("dateAdded"):
                try:
                    date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                except:
                    date_added = datetime.now()

            # Clean and Validate IDs
            def clean_id(val, valid_set):
                if val is None or val == 0: return None
                v = int(val)
                return v if v in valid_set else None

            hospital_type_id = clean_id(item.get("hospitalTypeId"), type_ids)
            state_id = clean_id(item.get("stateId"), state_ids)
            lga_id = clean_id(item.get("lgaId"), lga_ids)

            hospital_data = {
                "id": item["id"],
                "name": item["name"],
                "hospital_type_id": hospital_type_id,
                "state_id": state_id,
                "lga_id": lga_id,
                "location": item.get("location"),
                "address1": item.get("address1"),
                "address2": item.get("address2"),
                "landmark": item.get("landmark"),
                "date_added": date_added
            }
            to_insert.append(hospital_data)

        print(f"🚀 Starting batch insertion of {len(to_insert)} hospitals...")
        BATCH_SIZE = 100
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            stmt = insert(Hospital).values(chunk)
            
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in Hospital.__table__.columns
                if c.name not in ['id']
            }
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=update_dict
            )
            
            try:
                await session.execute(stmt)
                await session.commit()
                total_added += len(chunk)
                print(f"✅ Batch {i//BATCH_SIZE + 1} processed. ({total_added}/{len(to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(Hospital).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping hospital ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")
        
        print(f"🏁 Done! Successfully seeded {total_added} hospitals.")

if __name__ == "__main__":
    asyncio.run(seed_hospitals())
