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
from app.models.transfer_form import TransferForm
from app.models.incident import Incident
from app.models.run_sheet import RunSheet
from app.models.hospital import Hospital
from app.models.user import User

async def seed_transfer_forms():
    json_path = os.path.join(os.path.dirname(__file__), "formatted_transfer_form.json")
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found")
        return

    print(f"📂 Loading transfer forms from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        print("🔍 Pre-fetching incident, hospital, and run_sheet IDs for validation...")
        
        # Validations
        incidents_res = await session.execute(select(Incident.id))
        existing_incidents = set(incidents_res.scalars().all())

        hospitals_res = await session.execute(select(Hospital.id))
        existing_hospitals = set(hospitals_res.scalars().all())

        runsheets_res = await session.execute(select(RunSheet.id))
        existing_runsheets = set(runsheets_res.scalars().all())

        users_res = await session.execute(select(User.id))
        existing_users = {str(uid) for uid in users_res.scalars().all()}

        print(f"💼 Preparing {len(data)} Transfer Forms...")
        forms_to_insert = []
        for item in data:
            incident_id = item.get("incidentId")
            etc_id = item.get("etC_Id")
            run_sheet_id = item.get("runSheetId")

            # Validate required Foreign Keys
            if incident_id not in existing_incidents:
                continue
            if etc_id not in existing_hospitals:
                continue
            if run_sheet_id not in existing_runsheets:
                continue

            created_at_val = None
            date_str = item.get("dateAdded")
            if date_str:
                try:
                    created_at_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            medic_user_id = item.get("medicUserId")
            # If it's an empty string or '00000000-0000-0000-0000-000000000000', treat as None
            if not medic_user_id or medic_user_id == "00000000-0000-0000-0000-000000000000" or len(str(medic_user_id)) < 32:
                medic_user_id = None
            elif str(medic_user_id) not in existing_users:
                medic_user_id = None

            hospice_user_id = item.get("hospiceUserId")
            if not hospice_user_id or hospice_user_id == "00000000-0000-0000-0000-000000000000" or len(str(hospice_user_id)) < 32:
                hospice_user_id = None
            elif str(hospice_user_id) not in existing_users:
                hospice_user_id = None

            forms_to_insert.append({
                "id": item.get("id"),
                "incident_id": incident_id,
                "medic_user_id": medic_user_id,
                "hospice_user_id": hospice_user_id,
                "patient_id": item.get("patient_Id"),
                "patient_ids": item.get("patientIds") or [],
                "etc_id": etc_id,
                "run_sheet_id": run_sheet_id,
                "approve": item.get("approve", False),
                "created_at": created_at_val
            })

        print(f"🚀 Starting batch insertion of {len(forms_to_insert)} transfer forms...")
        BATCH_SIZE = 500
        total_forms_added = 0
        
        for i in range(0, len(forms_to_insert), BATCH_SIZE):
            chunk = forms_to_insert[i:i + BATCH_SIZE]
            stmt = insert(TransferForm).values(chunk)
            
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in TransferForm.__table__.columns
                if c.name not in ['id']
            }
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=update_dict
            )
            
            try:
                await session.execute(stmt)
                await session.commit()
                total_forms_added += len(chunk)
                print(f"✅ Batch {i//BATCH_SIZE + 1} processed. ({total_forms_added}/{len(forms_to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(TransferForm).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_forms_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping form ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")

        print(f"🏁 Done! Successfully seeded {total_forms_added} transfer forms.")

if __name__ == "__main__":
    asyncio.run(seed_transfer_forms())
