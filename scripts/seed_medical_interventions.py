import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.medical_intervention import MedicalIntervention
from app.models.patient import Patient


def safe_str(val):
    if val is None:
        return None
    return str(val)

def safe_int(val):
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except Exception:
        return None

async def seed_medical_interventions():
    json_path = os.path.join(os.path.dirname(__file__), "medicalIntervention.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Medical Interventions: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        # Get valid patient IDs to avoid FK violations
        valid_patient_ids = set((await session.execute(select(Patient.id))).scalars().all())
        print(f"📈 Valid Patient IDs in DB: {len(valid_patient_ids)}")

        print(f"🧐 Preparing {len(data)} medical interventions for seeding...")
        
        to_insert = []
        for item in data:
            patient_id = item.get("patientId")
            if patient_id not in valid_patient_ids:
                # We could skip or log, but usually we want to keep data integrity
                continue

            # Parse Dates
            date_added = None
            if item.get("dateAdded"):
                try:
                    date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                except Exception:
                    date_added = datetime.now()
            
            time_taken = None
            if item.get("timeTaken") and item.get("timeTaken") != "0001-01-01T00:00:00":
                try:
                    time_taken = datetime.fromisoformat(item["timeTaken"].replace("Z", "+00:00"))
                except Exception:
                    time_taken = None

            # Map fields to model with proper casting
            intervention_data = {
                "id": item.get("id"),
                "patient_id": patient_id,
                "is_alert": bool(item.get("isAlert", False)),
                "can_speak": bool(item.get("canSpeak", False)),
                "is_in_pain": bool(item.get("isInPain", False)),
                "un_responsive": bool(item.get("unResponsive", False)),
                "main_complaint": safe_str(item.get("mainComplaint")),
                "primary_survey": safe_str(item.get("primarySurvey")),
                "physical_examination_findings": safe_str(item.get("physicalExaminationFindings")),
                "iv_fluid_type": safe_str(item.get("ivFluidType")),
                "size_of_fluid": safe_str(item.get("sizeOfFluid")),
                "location_of_iv_infusion": safe_str(item.get("locationOfIvInfusion")),
                "total_iv_fluid_volume_given": safe_str(item.get("totalIvFluidVolumeGiven")),
                "oxygen": safe_str(item.get("oxygen")),
                "remarks": safe_str(item.get("remarks")),
                "pulse": safe_int(item.get("pulse")),
                "blood_pressure": safe_str(item.get("bloodPressure")),
                "resp": safe_int(item.get("resp")),
                "glucose": safe_int(item.get("glucose")),
                "sp02": safe_int(item.get("sp02")),
                "notes": safe_str(item.get("notes")),
                "medical_intervention_details": safe_str(item.get("mediicalIntervention")),
                "date_added": date_added,
                "time_taken": time_taken
            }
            to_insert.append(intervention_data)


        if not to_insert:
            print("🏁 No new medical interventions to seed.")
            return

        print(f"🚀 Starting batch insertion of {len(to_insert)} medical interventions...")
        
        BATCH_SIZE = 500
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            
            stmt = insert(MedicalIntervention).values(chunk)
            
            # Upsert logic
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in MedicalIntervention.__table__.columns
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
                print(f"❌ Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                # Optional: fallback to one-by-one if needed, but for now let's keep it simple
        
        print(f"🏁 Done! Successfully seeded {total_added} medical interventions.")

if __name__ == "__main__":
    asyncio.run(seed_medical_interventions())
