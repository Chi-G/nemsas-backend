import asyncio
import json
import os
import sys
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

# Ensure backend root is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.etc_intervention import EtcIntervention
from app.models.incident import Incident

async def seed_etc_interventions():
    interventions_json_path = os.path.join(os.path.dirname(__file__), "etc_interventions.json")
    if not os.path.exists(interventions_json_path):
        print(f"❌ {interventions_json_path} not found")
        return

    print(f"📂 Loading interventions from {interventions_json_path}...")
    with open(interventions_json_path, 'r') as f:
        extracted_interventions = json.load(f)

    async with SessionLocal() as session:
        # Pre-fetch existing incident IDs to optimize lookups
        print("🔍 Pre-fetching incident mappings for fast resolution...")
        incidents_res = await session.execute(select(Incident.id))
        existing_incidents = set(incidents_res.scalars().all())

        print(f"💼 Preparing {len(extracted_interventions)} Interventions...")
        interventions_to_insert = []
        for item in extracted_interventions:
            date_added_val = None
            date_str = item.get("dateAdded")
            if date_str:
                try:
                    date_added_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            incident_id = item.get("incident_Id")
            if incident_id not in existing_incidents:
                incident_id = None

            interventions_to_insert.append({
                "id": item["id"],
                "drug_id": item.get("drugId"),
                "medical_intervention": item.get("medicalIntervention"),
                "price": float(item.get("price") or 0.0),
                "dose": float(item.get("dose") or 0.0),
                "diagnosis": item.get("diagnosis"),
                "quantity": item.get("quantity"),
                "ambulance_id": item.get("ambulanceId"),
                "emergency_treatment_center_id": item.get("emergencyTreatmentCenterId"),
                "incident_id": incident_id,
                "date_added": date_added_val
            })

        print(f"🚀 Starting batch insertion of {len(interventions_to_insert)} interventions...")
        BATCH_SIZE = 500
        total_interventions_added = 0
        
        for i in range(0, len(interventions_to_insert), BATCH_SIZE):
            chunk = interventions_to_insert[i:i + BATCH_SIZE]
            stmt = insert(EtcIntervention).values(chunk)
            
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in EtcIntervention.__table__.columns
                if c.name not in ['id']
            }
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=update_dict
            )
            
            try:
                await session.execute(stmt)
                await session.commit()
                total_interventions_added += len(chunk)
                print(f"✅ Interventions Batch {i//BATCH_SIZE + 1} processed. ({total_interventions_added}/{len(interventions_to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Interventions Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(EtcIntervention).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_interventions_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping intervention ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")

        print(f"🏁 Done! Successfully seeded {total_interventions_added} interventions.")

if __name__ == "__main__":
    asyncio.run(seed_etc_interventions())
