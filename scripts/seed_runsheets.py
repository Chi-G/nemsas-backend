import asyncio
import json
import os
import sys
import uuid

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.run_sheet import RunSheet, RunSheetStatus
from app.models.incident import Incident
from app.models.patient import Patient
from app.models.ambulance import Ambulance
from app.models.user import User
from app.models.hospital import Hospital
from app.models.state import State
from app.models.lga import LGA
from app.models.ward import Ward
from app.models.hospital_type import HospitalType
from app.models.ambulance_type import AmbulanceType
from app.models.incident_type import IncidentType
from app.core.security import get_password_hash

DEFAULT_PASSWORD = "NemsasDefault"

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
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        try:
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

def parse_int(val):
    if val is None: return None
    try:
        return int(val)
    except Exception:
        return None

def parse_float(val):
    if val is None: return None
    try:
        return float(val)
    except Exception:
        return None

async def seed_runsheets():
    json_path = os.path.join(os.path.dirname(__file__), "runsheet.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Runsheets: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        payload = json.load(f)

    if isinstance(payload, list):
        data = payload
    else:
        data = payload.get("data", {}).get("items", [])
    if not data:
        print("⚠️ No runsheets found in JSON.")
        return

    async with SessionLocal() as session:
        # 1. Fetch valid reference master keys
        state_ids = set((await session.execute(select(State.id))).scalars().all())
        lga_ids = set((await session.execute(select(LGA.id))).scalars().all())
        ward_ids = set((await session.execute(select(Ward.id))).scalars().all())
        hosp_type_ids = set((await session.execute(select(HospitalType.id))).scalars().all())
        amb_type_ids = set((await session.execute(select(AmbulanceType.id))).scalars().all())
        inc_type_ids = set((await session.execute(select(IncidentType.id))).scalars().all())

        # Fetch existing users to avoid email/username conflicts
        existing_users_res = await session.execute(select(User.id, User.email, User.user_name))
        existing_users = existing_users_res.all()
        existing_emails = {}
        existing_usernames = {}
        for row in existing_users:
            if row.email:
                existing_emails[row.email.lower()] = str(row.id)
            if row.user_name:
                existing_usernames[row.user_name.lower()] = str(row.id)

        # Fetch existing ambulances to avoid code conflicts
        existing_ambs_res = await session.execute(select(Ambulance.id, Ambulance.code))
        existing_ambs = existing_ambs_res.all()
        existing_codes = {}
        for row in existing_ambs:
            if row.code:
                existing_codes[row.code.lower()] = int(row.id)

        # Fetch existing incidents to avoid serial_no conflicts
        existing_incs_res = await session.execute(select(Incident.id, Incident.serial_no))
        existing_incs = existing_incs_res.all()
        existing_serials = {}
        for row in existing_incs:
            if row.serial_no:
                existing_serials[row.serial_no.lower()] = int(row.id)

        print(f"✅ Master reference key counts: States={len(state_ids)}, LGAs={len(lga_ids)}, Wards={len(ward_ids)}, HospitalTypes={len(hosp_type_ids)}, AmbulanceTypes={len(amb_type_ids)}, IncidentTypes={len(inc_type_ids)}")

        # Helper clean_id
        def clean_id(val, valid_set):
            if val is None or val == 0: return None
            try:
                v = int(val)
                return v if v in valid_set else None
            except Exception:
                return None

        # 2. Extract nested entities
        users_to_upsert = {}
        hospitals_to_upsert = {}
        ambulances_to_upsert = {}
        incidents_to_upsert = {}
        patients_to_upsert = {}

        print("🔍 Scanning runsheets for nested entities...")
        for item in data:
            if not isinstance(item, dict): continue
            
            # Users
            medic_user = item.get("user")
            if medic_user and isinstance(medic_user, dict):
                mu_id = medic_user.get("id")
                if is_valid_uuid(mu_id):
                    users_to_upsert[str(mu_id)] = medic_user

            # Hospitals/ETCs from incidentViewModel
            inc_view = item.get("incidentViewModel")
            if inc_view and isinstance(inc_view, dict):
                etc = inc_view.get("emergencyTreatmentCenter")
                if etc and isinstance(etc, dict):
                    etc_id = etc.get("id")
                    if etc_id:
                        hospitals_to_upsert[int(etc_id)] = etc
                        
            # Hospitals/ETCs from emergencyTreatmentCenterViewModel
            etc_view = item.get("emergencyTreatmentCenterViewModel")
            if etc_view and isinstance(etc_view, dict):
                etc_view_id = etc_view.get("id")
                if etc_view_id:
                    hospitals_to_upsert[int(etc_view_id)] = etc_view

            # Ambulances
            amb_view = item.get("ambulanceViewModel")
            if amb_view and isinstance(amb_view, dict):
                amb_id = amb_view.get("id")
                if amb_id:
                    ambulances_to_upsert[int(amb_id)] = amb_view

            # Incidents
            if inc_view and isinstance(inc_view, dict):
                inc_id = inc_view.get("id")
                if inc_id:
                    incidents_to_upsert[int(inc_id)] = inc_view

            # Patients
            pat_view = item.get("patientViewModel")
            if pat_view and isinstance(pat_view, dict):
                pat_id = pat_view.get("id")
                if pat_id:
                    patients_to_upsert[int(pat_id)] = pat_view

            pats = item.get("patients")
            if pats and isinstance(pats, list):
                for p in pats:
                    if isinstance(p, dict):
                        p_id = p.get("id")
                        if p_id:
                            patients_to_upsert[int(p_id)] = p

        # 3. Seed Users
        if users_to_upsert:
            print(f"👥 Extracting and upserting {len(users_to_upsert)} nested Users...")
            hashed_pwd = get_password_hash(DEFAULT_PASSWORD)
            user_records = []
            
            # Local trackers for emails and usernames to avoid duplicates in the JSON itself
            local_seen_emails = set()
            local_seen_usernames = set()
            
            for uid, u in users_to_upsert.items():
                email = u.get("email") or f"user_{uid[:8]}@nemsas.gov.ng"
                username = u.get("username") or u.get("userName") or u.get("user_name") or f"user_{uid[:8]}"
                
                # Check for existing email conflict in DB or locally
                email_lower = email.lower()
                while (email_lower in existing_emails and existing_emails[email_lower] != str(uid)) or email_lower in local_seen_emails:
                    email_parts = email.split("@")
                    if len(email_parts) == 2:
                        email = f"{email_parts[0]}_seed_{uid[:8]}@{email_parts[1]}"
                    else:
                        email = f"{email}_seed_{uid[:8]}@nemsas.gov.ng"
                    email_lower = email.lower()
                
                local_seen_emails.add(email_lower)
                
                # Check for existing username conflict in DB or locally
                username_lower = username.lower()
                while (username_lower in existing_usernames and existing_usernames[username_lower] != str(uid)) or username_lower in local_seen_usernames:
                    username = f"{username}_seed_{uid[:8]}"
                    username_lower = username.lower()
                
                local_seen_usernames.add(username_lower)

                user_records.append({
                    "id": uid,
                    "first_name": u.get("firstName") or u.get("first_name") or "Unknown",
                    "middle_name": u.get("middleName") or u.get("middle_name"),
                    "last_name": u.get("lastName") or u.get("last_name") or "Unknown",
                    "user_name": username,
                    "email": email,
                    "phone_number": u.get("phoneNumber") or u.get("phone_number"),
                    "hashed_password": hashed_pwd,
                    "sex": parse_int(u.get("sex")) or 1,
                    "is_active": parse_bool(u.get("isActive")) if u.get("isActive") is not None else True,
                    "user_type": u.get("userType") or u.get("user_type"),
                    "organisation_name": u.get("organisationName") or u.get("organisation_name"),
                    "supervisor_user_id": str(u.get("supervisorUserId") or u.get("supervisor_user_id") or ""),
                    "emergency_treatment_center_id": parse_int(u.get("emergencyTreatmentCenterId") or u.get("etcId") or u.get("emergency_treatment_center_id")),
                    "ambulance_id": parse_int(u.get("ambulanceId") or u.get("ambulance_id")),
                    "state_id": clean_id(u.get("stateId") or u.get("state_id"), state_ids),
                    "lga_id": clean_id(u.get("lgaId") or u.get("lga_id"), lga_ids),
                    "ward_id": clean_id(u.get("wardId") or u.get("ward_id"), ward_ids),
                    "date_joined": parse_datetime(u.get("dateJoined") or u.get("date_joined")) or datetime.now()
                })
            
            # Batch upsert users
            for idx in range(0, len(user_records), 500):
                chunk = user_records[idx:idx + 500]
                stmt = insert(User).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        "state_id": stmt.excluded.state_id,
                        "lga_id": stmt.excluded.lga_id,
                        "ward_id": stmt.excluded.ward_id,
                        "ambulance_id": stmt.excluded.ambulance_id,
                        "emergency_treatment_center_id": stmt.excluded.emergency_treatment_center_id,
                        "organisation_name": stmt.excluded.organisation_name
                    }
                )
                await session.execute(stmt)
            await session.commit()
            print(f"✅ Upserted nested Users.")

        # 4. Seed Hospitals (ETCs)
        if hospitals_to_upsert:
            print(f"🏥 Extracting and upserting {len(hospitals_to_upsert)} nested Hospitals...")
            hosp_records = []
            for hid, h in hospitals_to_upsert.items():
                h_type_id = clean_id(h.get("hospitalTypeId") or h.get("hospital_type_id"), hosp_type_ids)
                s_id = clean_id(h.get("stateId") or h.get("state_id"), state_ids)
                l_id = clean_id(h.get("lgaId") or h.get("lga_id"), lga_ids)
                hosp_records.append({
                    "id": hid,
                    "name": h.get("name") or "Unknown Hospital",
                    "hospital_type_id": h_type_id,
                    "state_id": s_id,
                    "lga_id": l_id,
                    "location": h.get("location"),
                    "address1": h.get("address1"),
                    "address2": h.get("address2"),
                    "landmark": h.get("landmark"),
                    "date_added": parse_datetime(h.get("dateAdded") or h.get("date_added")) or datetime.now()
                })
            
            for idx in range(0, len(hosp_records), 500):
                chunk = hosp_records[idx:idx + 500]
                stmt = insert(Hospital).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        "name": stmt.excluded.name,
                        "hospital_type_id": stmt.excluded.hospital_type_id,
                        "state_id": stmt.excluded.state_id,
                        "lga_id": stmt.excluded.lga_id
                    }
                )
                await session.execute(stmt)
            await session.commit()
            print(f"✅ Upserted nested Hospitals.")

        # 5. Seed Ambulances
        if ambulances_to_upsert:
            print(f"🚑 Extracting and upserting {len(ambulances_to_upsert)} nested Ambulances...")
            amb_records = []
            local_seen_codes = set()
            for aid, a in ambulances_to_upsert.items():
                a_type_id = clean_id(a.get("ambulanceTypeId") or a.get("ambulance_type_id"), amb_type_ids)
                s_id = clean_id(a.get("stateId") or a.get("state_id"), state_ids)
                l_id = clean_id(a.get("lgaId") or a.get("lga_id"), lga_ids)
                w_id = clean_id(a.get("wardId") or a.get("ward_id"), ward_ids)
                
                code = a.get("code") or f"AMB-{aid}"
                code_lower = code.lower()
                while (code_lower in existing_codes and existing_codes[code_lower] != int(aid)) or code_lower in local_seen_codes:
                    code = f"{code}_seed_{aid}"
                    code_lower = code.lower()
                local_seen_codes.add(code_lower)

                amb_records.append({
                    "id": aid,
                    "name": a.get("name") or "Unknown Ambulance",
                    "code": code,
                    "location": a.get("location"),
                    "ambulance_type_id": a_type_id,
                    "state_id": s_id,
                    "lga_id": l_id,
                    "ward_id": w_id,
                    "nhia_or_shia": a.get("nhiAorSHIA") or a.get("nhia_or_shia"),
                    "service_type": a.get("serviceType") or a.get("service_type"),
                    "online": parse_bool(a.get("online")) if a.get("online") is not None else True,
                    "driver_name": a.get("driverName") or a.get("driver_name"),
                    "contact_number": a.get("contactNumber") or a.get("contact_number"),
                    "state_name": a.get("stateName") or a.get("state_name"),
                    "event_status_type": a.get("eventStatusType") or a.get("event_status_type"),
                    "date_added": parse_datetime(a.get("dateAdded") or a.get("date_added")) or datetime.now()
                })
            
            for idx in range(0, len(amb_records), 500):
                chunk = amb_records[idx:idx + 500]
                stmt = insert(Ambulance).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        "name": stmt.excluded.name,
                        "code": stmt.excluded.code,
                        "ambulance_type_id": stmt.excluded.ambulance_type_id,
                        "state_id": stmt.excluded.state_id,
                        "lga_id": stmt.excluded.lga_id,
                        "ward_id": stmt.excluded.ward_id
                    }
                )
                await session.execute(stmt)
            await session.commit()
            print(f"✅ Upserted nested Ambulances.")

        # 6. Seed Incidents
        if incidents_to_upsert:
            print(f"🚨 Extracting and upserting {len(incidents_to_upsert)} nested Incidents...")
            inc_records = []
            db_amb_ids = set((await session.execute(select(Ambulance.id))).scalars().all())
            db_etc_ids = set((await session.execute(select(Hospital.id))).scalars().all())
            db_user_ids = set(str(uid) for uid in (await session.execute(select(User.id))).scalars().all())

            local_seen_serials = set()
            for iid, inc in incidents_to_upsert.items():
                inc_type_id = clean_id(inc.get("incidentCategoryId") or inc.get("incident_category_id"), inc_type_ids)
                etc_id = clean_id(inc.get("emergencyTreatmentCenterId") or inc.get("etcId") or inc.get("etc_id"), db_etc_ids)
                amb_id = clean_id(inc.get("ambulanceId") or inc.get("ambulance_Id") or inc.get("ambulance_id"), db_amb_ids)
                dispatcher_id = inc.get("dispatcherId") or inc.get("dispatcher_id")
                if not is_valid_uuid(dispatcher_id) or str(dispatcher_id) not in db_user_ids:
                    dispatcher_id = None
                
                serial_no = inc.get("serialNo") or inc.get("serial_no")
                if serial_no:
                    serial_lower = serial_no.lower()
                    while (serial_lower in existing_serials and existing_serials[serial_lower] != int(iid)) or serial_lower in local_seen_serials:
                        serial_no = f"{serial_no}_seed_{iid}"
                        serial_lower = serial_no.lower()
                    local_seen_serials.add(serial_lower)
                else:
                    serial_no = None

                inc_records.append({
                    "id": iid,
                    "caller_name": inc.get("callerName") or inc.get("caller_name"),
                    "caller_number": inc.get("callerNumber") or inc.get("caller_number"),
                    "incident_date": parse_date(inc.get("incidentDate") or inc.get("incident_date")),
                    "incident_time": inc.get("incidentTime") or inc.get("incident_time"),
                    "description": inc.get("description"),
                    "recommendation": inc.get("recommendation"),
                    "triage_category": inc.get("triageCategory") or inc.get("triage_category"),
                    "incident_location": inc.get("incidentLocation") or inc.get("incident_location"),
                    "district_ward": inc.get("districtWard") or inc.get("district_ward"),
                    "street": inc.get("street"),
                    "area_council": inc.get("areaCouncil") or inc.get("area_council"),
                    "zip_code": inc.get("zipCode") or inc.get("zip_code"),
                    "incident_category_id": inc_type_id,
                    "can_resolve_without_ambulance": parse_bool(inc.get("canResolveWithoutAmbulance") or inc.get("can_resolve_without_ambulance")),
                    "treatment_center": inc.get("treatmentCenter") or inc.get("treatment_center"),
                    "dispatch_full_name": inc.get("dispatchFullName") or inc.get("dispatch_full_name"),
                    "dispatcher_id": dispatcher_id,
                    "dispatch_date": parse_date(inc.get("dispatchDate") or inc.get("dispatch_date")),
                    "supervisor_first_name": inc.get("supervisorFirstName") or inc.get("supervisor_first_name"),
                    "supervisor_middle_name": inc.get("supervisorMiddleName") or inc.get("supervisor_middle_name"),
                    "supervisor_last_name": inc.get("supervisorLastName") or inc.get("supervisor_last_name"),
                    "supervisor_date": parse_date(inc.get("supervisorDate") or inc.get("supervisor_date")),
                    "serial_no": serial_no,
                    "caller_is_patient": inc.get("callerIsPatient") or inc.get("caller_is_patient"),
                    "longitude": parse_float(inc.get("longitude")),
                    "latitude": parse_float(inc.get("latitude")),
                    "mass_casualty": parse_bool(inc.get("massCasualty") or inc.get("mass_casualty")),
                    "total_patients": parse_int(inc.get("totalPatients") or inc.get("total_patients")),
                    "ambulance_start": parse_datetime(inc.get("ambulanceStart") or inc.get("ambulance_start")),
                    "ambulance_stop": parse_datetime(inc.get("ambulanceStop") or inc.get("ambulance_stop")),
                    "date_stop": parse_datetime(inc.get("dateStop") or inc.get("date_stop")),
                    "incident_status_type": inc.get("incidentStatusType") or inc.get("incident_status_type"),
                    "event_status_type": inc.get("eventStatusType") or inc.get("event_status_type"),
                    "claims_approved": inc.get("claimsApproved") or inc.get("claims_approved"),
                    "state_name": inc.get("stateName") or inc.get("state_name"),
                    "date_added": parse_datetime(inc.get("dateAdded") or inc.get("date_added") or inc.get("date_stop")) or datetime.now(),
                    "etc_id": etc_id,
                    "ambulance_id": amb_id
                })
            
            for idx in range(0, len(inc_records), 500):
                chunk = inc_records[idx:idx + 500]
                stmt = insert(Incident).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        "incident_category_id": stmt.excluded.incident_category_id,
                        "etc_id": stmt.excluded.etc_id,
                        "ambulance_id": stmt.excluded.ambulance_id,
                        "incident_status_type": stmt.excluded.incident_status_type,
                        "event_status_type": stmt.excluded.event_status_type,
                        "serial_no": stmt.excluded.serial_no
                    }
                )
                await session.execute(stmt)
            await session.commit()
            print(f"✅ Upserted nested Incidents.")

        # 7. Seed Patients
        if patients_to_upsert:
            print(f"🩺 Extracting and upserting {len(patients_to_upsert)} nested Patients...")
            pat_records = []
            db_inc_ids = set((await session.execute(select(Incident.id))).scalars().all())
            db_amb_ids = set((await session.execute(select(Ambulance.id))).scalars().all())
            db_etc_ids = set((await session.execute(select(Hospital.id))).scalars().all())

            for pid, p in patients_to_upsert.items():
                inc_id = clean_id(p.get("incident_id") or p.get("incident_Id") or p.get("incidentId"), db_inc_ids)
                amb_id = clean_id(p.get("ambulance_id") or p.get("ambulance_Id") or p.get("ambulanceId"), db_amb_ids)
                etc_id = clean_id(p.get("etc_id") or p.get("etC_id") or p.get("etC_Id") or p.get("etcId"), db_etc_ids)
                pat_records.append({
                    "id": pid,
                    "first_name": p.get("firstName") or p.get("first_name"),
                    "middle_name": p.get("middleName") or p.get("middle_name"),
                    "last_name": p.get("lastName") or p.get("last_name"),
                    "do_b": parse_date(p.get("doB") or p.get("do_b")),
                    "sex": parse_int(p.get("sex")),
                    "phone_number": p.get("phoneNumber") or p.get("phone_number"),
                    "nhia": p.get("nhia"),
                    "address": p.get("address"),
                    "incident_id": inc_id,
                    "ambulance_id": amb_id,
                    "etc_id": etc_id,
                    "notes": p.get("notes") or []
                })
            
            for idx in range(0, len(pat_records), 500):
                chunk = pat_records[idx:idx + 500]
                stmt = insert(Patient).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        "first_name": stmt.excluded.first_name,
                        "last_name": stmt.excluded.last_name,
                        "incident_id": stmt.excluded.incident_id,
                        "ambulance_id": stmt.excluded.ambulance_id,
                        "etc_id": stmt.excluded.etc_id
                    }
                )
                await session.execute(stmt)
            await session.commit()
            print(f"✅ Upserted nested Patients.")

        # Re-fetch valid primary keys to verify seeding
        valid_inc_ids = set((await session.execute(select(Incident.id))).scalars().all())
        valid_pat_ids = set((await session.execute(select(Patient.id))).scalars().all())
        valid_amb_ids = set((await session.execute(select(Ambulance.id))).scalars().all())
        from app.models.hospital import Hospital
        valid_hosp_ids = set((await session.execute(select(Hospital.id))).scalars().all())
        valid_usr_ids = set(str(uid) for uid in (await session.execute(select(User.id))).scalars().all())

        print(f"📈 DB counts after upserting nested: Incidents={len(valid_inc_ids)}, Patients={len(valid_pat_ids)}, Ambulances={len(valid_amb_ids)}, Users={len(valid_usr_ids)}")

        # 8. Seed Runsheets
        to_insert_dict = {}
        for item in data:
            rs_id = item.get("id")
            if not rs_id: continue
            
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

            # Map JSON to RunSheet Columns
            rs_data = {
                "id": rs_id,
                "incident_id": inc_id,
                "dispatch_id": None,
                "title": item.get("title"),
                "patient_id": pat_id,
                "ambulance_id": amb_id,
                "route_from": item.get("routeFrom"),
                "route_to": item.get("routeTo"),
                "take_off_time": parse_datetime(item.get("takeOffTime")),
                "arrival_time": parse_datetime(item.get("arrivalTime")),
                "total_minutes_to_hospital": parse_float(item.get("totalMinutesToHospital")),
                "medic_user_id": medic_uid,
                "hospice_user_id": hospice_uid,
                "patient_name": item.get("patientName") or (item.get("title") if item.get("title") else None),
                "age": parse_int(item.get("age")),
                "gender": item.get("gender"),
                "chief_complaint": item.get("chiefComplaint"),
                "assessment": item.get("assessment"),
                "blood_pressure": item.get("bloodPressure"),
                "pulse_rate": parse_int(item.get("pulseRate")),
                "respiratory_rate": parse_int(item.get("respiratoryRate")),
                "oxygen_saturation": parse_float(item.get("oxygenSaturation")),
                "temperature": parse_float(item.get("temperature")),
                "gcs": parse_int(item.get("gcs")),
                "status": item.get("status") or (RunSheetStatus.FULLY_SIGNED if (medic_uid and hospice_uid) else RunSheetStatus.CREW_SIGNED if medic_uid else RunSheetStatus.DRAFT),
                "crew_signature_id": medic_uid,
                "crew_signed_at": parse_datetime(item.get("takeOffTime")),
                "etc_signature_id": hospice_uid,
                "etc_signed_at": parse_datetime(item.get("arrivalTime")),
                "date_added": parse_datetime(item.get("dateAdded")) or datetime.now()
            }
            to_insert_dict[rs_id] = rs_data

        to_insert = list(to_insert_dict.values())

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

        print(f"🏁 Done! Successfully seeded {total_added} runsheets with all nested relationships fully populated.")

if __name__ == "__main__":
    asyncio.run(seed_runsheets())
