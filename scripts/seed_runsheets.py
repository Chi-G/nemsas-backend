import asyncio
import json
import os
import sys
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.run_sheet import RunSheet, RunSheetStatus
from app.models.incident import Incident
from app.models.patient import Patient
from app.models.ambulance import Ambulance
from app.models.user import User

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def seed_runsheets():
    json_path = os.path.join(os.path.dirname(__file__), "runsheet.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Runsheets: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        payload = json.load(f)

    data = payload if isinstance(payload, list) else payload.get("data", {}).get("items", [])
    if not data:
        print("⚠️ No runsheets found in JSON.")
        return

    async with SessionLocal() as session:
        # Fetch valid primary keys to prevent FK constraint violations
        valid_inc_ids = set((await session.execute(select(Incident.id))).scalars().all())
        valid_pat_ids = set((await session.execute(select(Patient.id))).scalars().all())
        valid_amb_ids = set((await session.execute(select(Ambulance.id))).scalars().all())
        from app.models.hospital import Hospital
        valid_hosp_ids = set((await session.execute(select(Hospital.id))).scalars().all())
        valid_usr_ids = set(str(uid) for uid in (await session.execute(select(User.id))).scalars().all())

        print(f"📈 DB counts for validation: Incidents={len(valid_inc_ids)}, Patients={len(valid_pat_ids)}, Ambulances={len(valid_amb_ids)}, Users={len(valid_usr_ids)}")

        to_insert = []
        for item in data:
            rs_id = item.get("id")
            
            # FK Sanitization
            inc_id = item.get("incidentId")
            if inc_id not in valid_inc_ids:
                inc_id = None
                
            pat_id = item.get("patientId")
            if isinstance(pat_id, list):
                pat_id = [p for p in pat_id if p in valid_pat_ids]
            elif pat_id in valid_pat_ids:
                pat_id = [pat_id]
            else:
                pat_id = []
                
            amb_id = item.get("ambulanceId")
            if amb_id not in valid_amb_ids:
                amb_id = None
                
            medic_uid = item.get("medicUserId")
            if medic_uid not in valid_usr_ids:
                medic_uid = None
                
            hospice_uid = item.get("hospiceUserId")
            if hospice_uid not in valid_usr_ids:
                hospice_uid = None
                
            etc_id = item.get("emergencyTreatmentCenterId")
            if etc_id not in valid_hosp_ids:
                etc_id = None

            # Date Parsing
            take_off_time = None
            if item.get("takeOffTime"):
                try:
                    take_off_time = datetime.fromisoformat(item["takeOffTime"].replace("Z", "+00:00"))
                except Exception:
                    pass

            arrival_time = None
            if item.get("arrivalTime"):
                try:
                    arrival_time = datetime.fromisoformat(item["arrivalTime"].replace("Z", "+00:00"))
                except Exception:
                    pass

            date_added = None
            if item.get("dateAdded"):
                try:
                    date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                except Exception:
                    pass

            # Map JSON to RunSheet Columns
            rs_data = {
                "id": rs_id,
                "incident_id": inc_id,
                "dispatch_id": None, # Nullable or mapped separately
                "title": item.get("title"),
                "patient_id": pat_id,
                "ambulance_id": amb_id,
                "route_from": item.get("routeFrom"),
                "route_to": item.get("routeTo"),
                "take_off_time": take_off_time,
                "arrival_time": arrival_time,
                "total_minutes_to_hospital": float(item.get("totalMinutesToHospital")) if item.get("totalMinutesToHospital") is not None else None,
                "emergency_treatment_center_id": etc_id,
                "price": float(item.get("price")) if item.get("price") is not None else None,
                "medic_user_id": medic_uid,
                "hospice_user_id": hospice_uid,
                "patient_name": item.get("patientName") or (item.get("title") if item.get("title") else None),
                "age": item.get("age"),
                "gender": item.get("gender"),
                "chief_complaint": item.get("chiefComplaint"),
                "assessment": item.get("assessment"),
                "blood_pressure": item.get("bloodPressure"),
                "pulse_rate": item.get("pulseRate"),
                "respiratory_rate": item.get("respiratoryRate"),
                "oxygen_saturation": float(item.get("oxygenSaturation")) if item.get("oxygenSaturation") is not None else None,
                "temperature": float(item.get("temperature")) if item.get("temperature") is not None else None,
                "gcs": item.get("gcs"),
                "status": RunSheetStatus.FULLY_SIGNED if (medic_uid and hospice_uid) else RunSheetStatus.CREW_SIGNED if medic_uid else RunSheetStatus.DRAFT,
                "crew_signature_id": medic_uid,
                "crew_signed_at": take_off_time,
                "etc_signature_id": hospice_uid,
                "etc_signed_at": arrival_time,
                "date_added": date_added or datetime.now()
            }
            to_insert.append(rs_data)

        if not to_insert:
            print("🏁 No new runsheets to seed.")
            return

        print(f"🚀 Starting batch insertion of {len(to_insert)} runsheets...")
        
        BATCH_SIZE = 200
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            
            stmt = insert(RunSheet).values(chunk)
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in RunSheet.__table__.columns
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
                        inner_stmt = insert(RunSheet).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k not in ['id', 'created_at']}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping Runsheet {single_item.get('id')}: {str(inner_e).splitlines()[0]}")

        print(f"🏁 Done! Successfully seeded {total_added} runsheets.")

if __name__ == "__main__":
    asyncio.run(seed_runsheets())
