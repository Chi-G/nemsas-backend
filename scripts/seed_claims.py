import asyncio
import json
import os
import sys
import re
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

# Ensure backend root is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.etc_intervention import EtcIntervention
from app.models.incident import Incident
from app.models.patient import Patient

async def seed_claims():
    claims_json_path = os.path.join(os.path.dirname(__file__), "extracted_claims_new.json")
    if not os.path.exists(claims_json_path):
        print(f"❌ {claims_json_path} not found")
        return

    with open(claims_json_path, 'r') as f:
        claims_data = json.load(f)

    # Skipping intervention generation to avoid overwriting etc_interventions.json

    async with SessionLocal() as session:
        # Pre-fetch existing incident IDs and their corresponding patient IDs to optimize lookups
        print("🔍 Pre-fetching incident and patient mappings for fast resolution...")
        incidents_res = await session.execute(select(Incident.id))
        existing_incidents = set(incidents_res.scalars().all())

        patients_res = await session.execute(
            select(Patient.id, Patient.incident_id).filter(Patient.incident_id.isnot(None))
        )
        patient_map = {row.incident_id: row.id for row in patients_res.fetchall()}

        print(f"💼 Preparing {len(claims_data)} Claims...")
        claims_to_insert = []
        for item in claims_data:
            title = item.get("title", "")
            
            # Extract incident_id from title
            incident_id = None
            patient_id = None
            match = re.search(r'incident\s+(\d+)', title, re.IGNORECASE)
            if match:
                extracted_id = int(match.group(1))
                if extracted_id in existing_incidents:
                    incident_id = extracted_id
                    patient_id = patient_map.get(extracted_id)

            claims_to_insert.append({
                "id": item["id"],
                "title": item.get("title"),
                "patient_name": item.get("patientName"),
                "ambulance_type": item.get("ambulanceType"),
                "incident_category": item.get("incidentCategory"),
                "nhia": item.get("nhia"),
                "location": item.get("location"),
                "service_provider": item.get("serviceProvider"),
                "distance_covered": float(item.get("distanceCovered") or 0.0),
                "total_price": float(item.get("totalPrice") or 0.0),
                "incident_date": item.get("incidentDate"),
                "review": item.get("review"),
                "etc_review": item.get("etcReview"),
                "ambulance_claim_status": item.get("ambulanceClaimStatus") or item.get("ambulance_claim_status", "New"),
                "etc_claim_status": item.get("etcClaimStatus") or item.get("etc_claim_status", "New"),
                "claim_type": "ETC" if item.get("drugsList") else "Ambulance",
                "incident_id": incident_id,
                "patient_id": patient_id
            })

        print(f"🚀 Starting batch insertion of {len(claims_to_insert)} claims...")
        BATCH_SIZE = 500
        total_claims_added = 0
        
        for i in range(0, len(claims_to_insert), BATCH_SIZE):
            chunk = claims_to_insert[i:i + BATCH_SIZE]
            stmt = insert(Claim).values(chunk)
            
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in Claim.__table__.columns
                if c.name not in ['id', 'created_at', 'updated_at']
            }
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=update_dict
            )
            
            try:
                await session.execute(stmt)
                await session.commit()
                total_claims_added += len(chunk)
                print(f"✅ Claims Batch {i//BATCH_SIZE + 1} processed. ({total_claims_added}/{len(claims_to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Claims Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(Claim).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_claims_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping claim ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")

        print(f"🏁 Done! Successfully seeded {total_claims_added} claims.")

if __name__ == "__main__":
    asyncio.run(seed_claims())
