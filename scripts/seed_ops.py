import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from uuid import UUID

sys.path.append(os.getcwd())

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text

from app.db.session import SessionLocal
import app.models.base  # Ensure all class registry is configured
from app.models.incident import Incident
from app.models.patient import Patient
from app.models.claim import Claim
from app.models.run_sheet import RunSheet
from app.models.monitoring import Monitoring

def parse_dt(val):
    if not val or str(val).startswith("0001-01-01"):
        return None
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except:
        return None

def parse_float(val):
    try:
        return float(val) if val is not None else None
    except:
        return None

def parse_int(val):
    try:
        return int(val) if val is not None else None
    except:
        return None

def is_uuid(val):
    if not val: return False
    try:
        UUID(str(val))
        return True
    except:
        return False

async def upsert_data(session, model, data_list, pk='id'):
    if not data_list:
        return 0
    
    inserted_count = 0
    for i in range(0, len(data_list), 100):
        chunk = data_list[i:i+100]
        stmt = pg_insert(model).values(chunk)
        # On conflict do nothing for primary keys, or update
        stmt = stmt.on_conflict_do_nothing(index_elements=[pk])
        try:
            await session.execute(stmt)
            await session.commit()
            inserted_count += len(chunk)
        except Exception as e:
            await session.rollback()
            # Fallback one by one
            for single in chunk:
                try:
                    stmt_single = pg_insert(model).values(single).on_conflict_do_nothing(index_elements=[pk])
                    await session.execute(stmt_single)
                    await session.commit()
                    inserted_count += 1
                except Exception:
                    await session.rollback()
                    pass
    return inserted_count

async def fix_sequence(session, table_name):
    """Resets standard serial sequence after manual ID insertion"""
    try:
        await session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), coalesce(max(id), 1)) FROM {table_name};"))
        await session.commit()
    except:
        await session.rollback()

async def seed_operational_data():
    scripts_dir = os.path.join(os.getcwd(), "scripts")
    print("🚀 Starting Operation Payload Seeding...")
    
    async with SessionLocal() as session:
        # ==========================================
        # 1. Seed Incidents & Extract Patients
        # ==========================================
        inc_path = os.path.join(scripts_dir, "incident.json")
        incident_recs = []
        patient_recs = {} # Map by ID to de-duplicate
        
        if os.path.exists(inc_path):
            with open(inc_path) as f:
                dat = json.load(f)
                items = dat.get("data", {}).get("items", []) if isinstance(dat, dict) else []
                
                for item in items:
                    inc_id = item.get("id")
                    if not inc_id: continue
                    
                    incident_recs.append({
                        "id": inc_id,
                        "serial_no": item.get("serialNo"),
                        "location_label": item.get("incidentLocation"),
                        "street": item.get("street"),
                        "district_ward": item.get("districtWard"),
                        "area_council": item.get("areaCouncil"),
                        "zip_code": item.get("zipCode"),
                        "latitude": parse_float(item.get("latitude")),
                        "longitude": parse_float(item.get("longitude")),
                        "caller_name": item.get("callerName"),
                        "caller_phone": item.get("callerNumber"),
                        "caller_is_patient": item.get("callerIsPatient"),
                        "incident_category": item.get("incidentCategory"),
                        "triage_category": item.get("triageCategory"),
                        "description": item.get("description"),
                        "recommendation": item.get("recommendation"),
                        "can_resolve_without_ambulance": item.get("canResolveWithoutAmbulance"),
                        "treatment_center": item.get("treatmentCenter"),
                        "dispatch_full_name": item.get("dispatchFullName"),
                        "dispatcher_id": item.get("dispatcherId") if is_uuid(item.get("dispatcherId")) else None,
                        "mass_casualty": bool(item.get("massCasualty")),
                        "total_patients": parse_int(item.get("totalPatients")),
                        "incident_date": str(item.get("incidentDate") or ""),
                        "incident_time": str(item.get("incidentTime") or ""),
                        "dispatch_date": str(item.get("dispatchDate") or ""),
                        "ambulance_start": parse_dt(item.get("ambulanceStart")),
                        "ambulance_stop": parse_dt(item.get("ambulanceStop")),
                        "date_added": parse_dt(item.get("dateAdded")) or datetime.now(timezone.utc),
                        "status": "Reported",
                    })
                    
                    # Extract Nested Patient
                    pvm = item.get("patientViewModel")
                    if pvm and pvm.get("id"):
                        p_id = pvm["id"]
                        if p_id not in patient_recs:
                            patient_recs[p_id] = {
                                "id": p_id,
                                "first_name": pvm.get("firstName"),
                                "middle_name": pvm.get("middleName"),
                                "last_name": pvm.get("lastName"),
                                "do_b": parse_dt(pvm.get("doB")),
                                "sex": pvm.get("sex"),
                                "phone_number": pvm.get("phoneNumber"),
                                "nhia": pvm.get("nhia"),
                                "address": pvm.get("address"),
                                "incident_id": inc_id, # Direct link found in Incident payload
                            }

            # Batch Insert Incidents first
            inc_count = await upsert_data(session, Incident, incident_recs)
            print(f"✅ Seeded {inc_count} Incidents.")
            await fix_sequence(session, "incidents")
            
            # Batch Insert Patients derived from Incidents
            p_count = await upsert_data(session, Patient, list(patient_recs.values()))
            print(f"✅ Seeded {p_count} Patients extracted from incident logs.")
            await fix_sequence(session, "patients")
        
        # ==========================================
        # 2. Seed Claims (Ambulance & ETC)
        # ==========================================
        claim_recs = []
        
        for cf in ["ambulance_claims.json", "etc_claims.json"]:
            claim_path = os.path.join(scripts_dir, cf)
            if not os.path.exists(claim_path): continue
            
            with open(claim_path) as f:
                c_dat = json.load(f)
                c_items = c_dat.get("data", {}).get("items", []) if isinstance(c_dat, dict) else []
                for c in c_items:
                    cid = c.get("id")
                    if not cid: continue
                    
                    # If nested patient is present but not inserted yet
                    p_info = c.get("patient")
                    p_id_ref = None
                    if p_info and p_info.get("id"):
                        p_id_ref = p_info.get("id")
                        # Ensure patient is in the patient_recs for downstream check? 
                        # Actually the previous block caught them, but let's insert new ones just in case
                        if p_id_ref not in patient_recs:
                            p_new = {
                                "id": p_id_ref,
                                "first_name": p_info.get("firstName"),
                                "middle_name": p_info.get("middleName"),
                                "last_name": p_info.get("lastName"),
                                "do_b": parse_dt(p_info.get("doB")),
                                "sex": p_info.get("sex"),
                                "phone_number": p_info.get("phoneNumber"),
                                "nhia": p_info.get("nhia"),
                            }
                            await upsert_data(session, Patient, [p_new])
                            patient_recs[p_id_ref] = p_new

                    # If incident exists inside the claim but is 0, use incidentViewModel id
                    c_inc_id = c.get("incidentId") or (c.get("incidentViewModel") or {}).get("id")

                    claim_recs.append({
                        "id": cid,
                        "title": c.get("title"),
                        "patient_name": c.get("patientName"),
                        "patient_id": p_id_ref,
                        "incident_id": c_inc_id if c_inc_id and c_inc_id != 0 else None,
                        "ambulance_type": c.get("ambulanceType"),
                        "incident_category": c.get("incidentCategory"),
                        "nhia": c.get("nhia"),
                        "location": c.get("location"),
                        "service_provider": c.get("serviceProvider"),
                        "incident_date": c.get("incidentDate"),
                        "total_price": parse_float(c.get("totalPrice")),
                        "distance_covered": parse_float(c.get("distanceCovered")),
                        "status": c.get("status") or "New",
                        "review": c.get("review"),
                        "etc_review": c.get("etcReview"),
                    })
        
        claims_inserted = await upsert_data(session, Claim, claim_recs)
        print(f"✅ Seeded {claims_inserted} Claims (Ambulance & ETC Combined).")
        await fix_sequence(session, "claims")

        # ==========================================
        # 3. Seed RunSheets
        # ==========================================
        rs_path = os.path.join(scripts_dir, "runsheet.json")
        rs_recs = []
        if os.path.exists(rs_path):
            with open(rs_path) as f:
                rs_dat = json.load(f)
                if isinstance(rs_dat, list):
                    rs_items = rs_dat
                elif isinstance(rs_dat, dict):
                    rs_items = rs_dat.get("data", {}).get("items", [])
                else:
                    rs_items = []
                for r in rs_items:
                    rid = r.get("id")
                    if not rid: continue
                    
                    amb_id = r.get("ambulanceId")
                    
                    rs_recs.append({
                        "id": rid,
                        "title": r.get("title"),
                        "incident_id": r.get("incidentId") if r.get("incidentId") != 0 else None,
                        "patient_id": r.get("patientId") if r.get("patientId") != 0 else None,
                        "ambulance_id": amb_id if amb_id and amb_id != 0 else None,
                        "route_from": r.get("routeFrom"),
                        "route_to": r.get("routeTo"),
                        "take_off_time": parse_dt(r.get("takeOffTime")),
                        "arrival_time": parse_dt(r.get("arrivalTime")),
                        "total_minutes_to_hospital": parse_int(r.get("totalMinutesToHospital")),
                        "medic_user_id": r.get("medicUserId") if is_uuid(r.get("medicUserId")) else None,
                        "hospice_user_id": r.get("hospiceUserId") if is_uuid(r.get("hospiceUserId")) else None,
                        "date_added": parse_dt(r.get("dateAdded")),
                    })
            rs_count = await upsert_data(session, RunSheet, rs_recs)
            print(f"✅ Seeded {rs_count} Run Sheets.")
            await fix_sequence(session, "run_sheets")

        # ==========================================
        # 4. Seed Monitoring Entries
        # ==========================================
        m_path = os.path.join(scripts_dir, "monitoring.json")
        m_recs = []
        if os.path.exists(m_path):
            with open(m_path) as f:
                m_items = json.load(f)
                if isinstance(m_items, list):
                    for m in m_items:
                        m_id = m.get("id")
                        if not m_id: continue
                        
                        m_recs.append({
                            "id": m_id,
                            "year": parse_int(m.get("year")),
                            "month": parse_int(m.get("month")),
                            "no_of_transport": parse_int(m.get("noOfTransport")),
                            "no_of_mamii_lgas": parse_int(m.get("noOfMamiiLGAs")),
                            "by_tricycle_ambulance": parse_int(m.get("byTricycleAmbulance")),
                            "by_nurtw_driver": parse_int(m.get("byNurtwDriver")),
                            "bls": parse_int(m.get("bls")),
                            "labor_transportation": parse_int(m.get("laborTransportation")),
                            "obstetric_transportation": parse_int(m.get("obstetricTransportation")),
                            "neonatal_transportation": parse_int(m.get("neonatalTransportation")),
                            "bemonc": parse_int(m.get("bemonc")),
                            "cemonc": parse_int(m.get("cemonc")),
                            "maternal_mortalities": parse_int(m.get("maternalMortalities")),
                            "neonatal_mortalities": parse_int(m.get("neonatalMortalities")),
                            "remark": m.get("remark"),
                            "state_id": m.get("stateId"),
                            "added_by": m.get("addedBy"),
                            "date_added": parse_dt(m.get("dateAdded")),
                        })
            m_count = await upsert_data(session, Monitoring, m_recs)
            print(f"✅ Seeded {m_count} Monitoring Evaluation Logs.")
            await fix_sequence(session, "monitoring_evaluations")

    print("🏁 All operations seeding procedures have concluded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_operational_data())
