import asyncio
import json
import os
import sys
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.patient import Patient
from app.models.incident import Incident

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def seed_patients():
    json_path = os.path.join(os.path.dirname(__file__), "patients.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Patients: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        # Get existing patients to skip
        existing_ids = set((await session.execute(select(Patient.id))).scalars().all())
        print(f"📈 Already in DB: {len(existing_ids)} patients.")
        
        # Get valid incident IDs to avoid FK violations
        valid_inc_ids = set((await session.execute(select(Incident.id))).scalars().all())
        print(f"📈 Valid Incident IDs in DB: {len(valid_inc_ids)}")

        print(f"🧐 Preparing {len(data)} patients for seeding (refreshing links)...")
        
        to_insert = []
        for item in data:
            patient_id = item.get("id")
            
            # Parse Date of Birth
            do_b = None
            if item.get("doB"):
                try:
                    do_b = datetime.fromisoformat(item["doB"].replace("Z", "+00:00")).date()
                except Exception:
                    do_b = None

            # Sanitize Incident ID
            inc_id = item.get("incident_id")
            if inc_id not in valid_inc_ids: inc_id = None

            # Map fields to model
            patient_data = {
                "id": patient_id,
                "first_name": item.get("firstName"),
                "middle_name": item.get("middleName"),
                "last_name": item.get("lastName"),
                "do_b": do_b,
                "sex": item.get("sex"),
                "phone_number": item.get("phoneNumber"),
                "nhia": item.get("nhia"),
                "address": item.get("address"),
                "incident_id": inc_id,
                "ambulance_id": item.get("ambulance_Id"),
                "etc_id": item.get("etC_id"),
                "notes": item.get("notes", [])
            }
            to_insert.append(patient_data)

        if not to_insert:
            print("🏁 No new patients to seed.")
            return

        print(f"🚀 Starting batch insertion of {len(to_insert)} patients...")
        
        # Batch size for large datasets
        BATCH_SIZE = 500
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            
            stmt = insert(Patient).values(chunk)
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in Patient.__table__.columns
                if c.name not in ['id', 'created_at']
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
                print(f"❌ Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(Patient).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k not in ['id', 'created_at']}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping Patient {single_item.get('id')}: {str(inner_e).splitlines()[0]}")

        print(f"🏁 Done! Successfully seeded {total_added} patients.")

if __name__ == "__main__":
    asyncio.run(seed_patients())
