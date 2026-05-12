import asyncio
import json
import os
import uuid
from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.incident_type import IncidentType

BATCH_SIZE = 500

def is_valid_uuid(val):
    if not val: return False
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def parse_date(date_str):
    if not date_str: return None
    try:
        # Handle "YYYY-MM-DD"
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        try:
            # Handle ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except Exception:
            return None

def parse_datetime(dt_str):
    if not dt_str or dt_str == "0001-01-01T00:00:00": return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def parse_bool(val):
    if val is None: return None
    if isinstance(val, bool): return val
    if isinstance(val, str):
        return val.lower() in ("yes", "true", "1")
    return bool(val)

async def seed_incidents():
    json_path = os.path.join(os.path.dirname(__file__), "incidentsNew.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Incidents: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        incidents_data = json.load(f)

    async with SessionLocal() as session:
        # Get all existing IDs to skip them
        result = await session.execute(select(Incident.id))
        existing_ids = set(result.scalars().all())
        print(f"📈 Total Incidents already in DB: {len(existing_ids)}")
        
        # Get all valid foreign keys to avoid violations
        amb_ids = set((await session.execute(select(Ambulance.id))).scalars().all())
        etc_ids = set((await session.execute(select(Hospital.id))).scalars().all())
        type_ids = set((await session.execute(select(IncidentType.id))).scalars().all())
        from app.models.user import User
        user_ids = set((await session.execute(select(User.id))).scalars().all())
        
        print(f"✅ Found {len(amb_ids)} ambulances, {len(etc_ids)} hospitals, {len(type_ids)} incident types, {len(user_ids)} users.")

        print(f"🧐 Cleaning and preparing incidents (skipping existing IDs)...")
        
        seen_ids = set()
        seen_serial_nos = set()
        to_insert = []
        
        for item in incidents_data:
            if not isinstance(item, dict): continue
            
            incident_id = item.get("id")
            serial_no = item.get("serialNo")
            
            # Skip if already in DB or seen in this run
            if incident_id in existing_ids: continue
            if incident_id in seen_ids: continue
            if serial_no and serial_no in seen_serial_nos: continue
            
            seen_ids.add(incident_id)
            if serial_no: seen_serial_nos.add(serial_no)

            # Sanitize Foreign Keys
            inc_type_id = item.get("incidentCategoryId")
            if inc_type_id not in type_ids: inc_type_id = None
            
            etc_id = item.get("etcId")
            if etc_id not in etc_ids: etc_id = None
            
            amb_id = item.get("ambulance_Id")
            if amb_id not in amb_ids: amb_id = None

            dispatcher_id = item.get("dispatcherId")
            if not is_valid_uuid(dispatcher_id) or uuid.UUID(str(dispatcher_id)) not in user_ids:
                dispatcher_id = None
            
            # Prepare data
            data = {
                "id": incident_id,
                "caller_name": item.get("callerName"),
                "caller_number": item.get("callerNumber"),
                "incident_date": parse_date(item.get("incidentDate")),
                "incident_time": item.get("incidentTime"),
                "description": item.get("description"),
                "recommendation": item.get("recommendation"),
                "triage_category": item.get("triageCategory"),
                "incident_location": item.get("incidentLocation"),
                "district_ward": item.get("districtWard"),
                "street": item.get("street"),
                "area_council": item.get("areaCouncil"),
                "zip_code": item.get("zipCode"),
                "incident_category_id": inc_type_id,
                "can_resolve_without_ambulance": parse_bool(item.get("canResolveWithoutAmbulance")),
                "treatment_center": item.get("treatmentCenter"),
                "dispatch_full_name": item.get("dispatchFullName"),
                "dispatcher_id": dispatcher_id,
                "dispatch_date": parse_date(item.get("dispatchDate")),
                "supervisor_first_name": item.get("supervisorFirstName"),
                "supervisor_middle_name": item.get("supervisorMiddleName"),
                "supervisor_last_name": item.get("supervisorLastName"),
                "supervisor_date": parse_date(item.get("supervisorDate")),
                "serial_no": serial_no,
                "caller_is_patient": item.get("callerIsPatient"),
                "longitude": item.get("longitude"),
                "latitude": item.get("latitude"),
                "mass_casualty": parse_bool(item.get("massCasualty")),
                "total_patients": item.get("totalPatients"),
                "ambulance_start": parse_datetime(item.get("ambulanceStart")),
                "ambulance_stop": parse_datetime(item.get("ambulanceStop")),
                "date_stop": parse_datetime(item.get("dateStop")),
                "incident_status_type": item.get("incidentStatusType"),
                "event_status_type": item.get("eventStatusType"),
                "claims_approved": item.get("claimsApproved"),
                "state_name": item.get("stateName"),
                "date_added": parse_datetime(item.get("dateAdded")),
                "etc_id": etc_id,
                "ambulance_id": amb_id
            }
            to_insert.append(data)

        print(f"🚀 Starting insertion of {len(to_insert)} unique incidents...")
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            
            # Prepare the ON CONFLICT statement correctly
            stmt = pg_insert(Incident).values(chunk)
            
            # Use the excluded row to update existing records
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in Incident.__table__.columns
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
                print(f"⚠️ Batch {i//BATCH_SIZE + 1} failed: {type(e).__name__}: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = pg_insert(Incident).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping Incident {single_item.get('id')} / {single_item.get('serial_no')}: {str(inner_e).splitlines()[0]}")
        
        print(f"🏁 Done! Successfully processed {total_added} incidents.")

if __name__ == "__main__":
    asyncio.run(seed_incidents())
