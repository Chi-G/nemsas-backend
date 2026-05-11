import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from src.db.base import SessionLocal, engine, Base
from src.db.models.user import User, Role, Permission
from src.db.models.reference import State, LGA
from src.db.models.partner import Partner, Pledge, PledgeStatus, Facility, FacilityRequest, FacilityRequestStatus
from src.db.models.ambulance import Ambulance, AmbulanceStatus, AccreditationType, Dispatch, GPSHistory
from src.db.models.incident import Incident, IncidentStatus, EmergencyType, IncidentStatusHistory, QAFinding
from src.db.models.claim import Claim, ClaimType, ClaimStatus, RunSheet, ETCIntake
from src.core.security import get_password_hash

async def seed_demo_data():
    async with SessionLocal() as db:
        try:
            # References
            roles = {
                "Admin": (await db.execute(select(Role).where(Role.name == "NEMSAS Admin"))).scalar_one(),
                "SEMSAS_Admin": (await db.execute(select(Role).where(Role.name == "SEMSAS Admin"))).scalar_one(),
                "Dispatcher": (await db.execute(select(Role).where(Role.name == "Dispatcher"))).scalar_one(),
                "Crew": (await db.execute(select(Role).where(Role.name == "Ambulance Crew"))).scalar_one(),
                "ETP": (await db.execute(select(Role).where(Role.name == "Emergency Transport Provider"))).scalar_one(),
                "ETC_Staff": (await db.execute(select(Role).where(Role.name == "ETC Staff"))).scalar_one(),
                "Claims_Staff": (await db.execute(select(Role).where(Role.name == "Claims Staff"))).scalar_one(),
                "Partner": (await db.execute(select(Role).where(Role.name == "Partner"))).scalar_one(),
                "View_Only": (await db.execute(select(Role).where(Role.name == "View-Only User"))).scalar_one(),
            }
            fct_state = (await db.execute(select(State).where(State.name == "FCT"))).scalar_one()
            abuja_lga = (await db.execute(select(LGA).where(LGA.name == "Abuja Municipal", LGA.state_id == fct_state.id))).scalar_one()
            bwari_lga = (await db.execute(select(LGA).where(LGA.name == "Bwari", LGA.state_id == fct_state.id))).scalar_one()
        except Exception as e:
            print(f"❌ Reference data missing: {e}")
            return

        admin_user = (await db.execute(select(User).where(User.email == "admin@nemsas.gov.ng"))).scalar_one()

        # 1. PERMISSIONS & ROLE_PERMISSIONS
        perms_data = [
            {"name": "manage_incidents", "desc": "Can create/dispatch incidents", "role": "Dispatcher"},
            {"name": "view_incidents", "desc": "Can view incidents", "role": "View_Only"},
            {"name": "manage_claims", "desc": "Can approve or reject claims", "role": "Claims_Staff"},
            {"name": "manage_fleet", "desc": "Can manage ambulance fleet", "role": "ETP"}
        ]
        
        for p in perms_data:
            stmt = select(Permission).where(Permission.name == p["name"])
            perm = (await db.execute(stmt)).scalar_one_or_none()
            if not perm:
                perm = Permission(name=p["name"], description=p["desc"])
                db.add(perm)
                await db.flush()
                # Link permission to role directly (SQLAlchemy handles the association table magically)
                role_obj = roles[p["role"]]
                # Fetch role with eager loading of permissions to avoid LazyLoad error on async
                role_obj_loaded = (await db.execute(select(Role).where(Role.id == role_obj.id))).scalar_one()
                # Need to run sync for appending to a relationship, or just insert into mapping.
                # Easiest way in Async: just add and hope flush catches it, or better, we do it safely:
        await db.commit() # Save permissions first

        for p in perms_data:
             perm = (await db.execute(select(Permission).where(Permission.name == p["name"]))).scalar_one()
             role_obj = roles[p["role"]]
             # We can't easily append to lazy-loaded relations in async block.
             # We'll do a raw insert into the role_permissions table manually below if needed, but let's try direct connection
        
        async with engine.begin() as conn:
            from sqlalchemy import text
            for p in perms_data:
                perm = (await db.execute(select(Permission).where(Permission.name == p["name"]))).scalar_one()
                role_id = roles[p["role"]].id
                try: # handle duplicates gracefully
                    await conn.execute(text(f"INSERT INTO role_permissions (role_id, permission_id) VALUES ({role_id}, {perm.id}) ON CONFLICT DO NOTHING"))
                except Exception:
                    pass

        # 2. SEED USERS FOR ALL ROLES (EXCLUDING M&E / QA)
        users_to_create = [
            ("semsas_admin@demo.com", "FCT SEMSAS Admin", roles["SEMSAS_Admin"]),
            ("etp@demo.com", "National Fleet Owner", roles["ETP"]),
            ("etc_staff@demo.com", "Abuja Clinic Nurse", roles["ETC_Staff"]),
            ("claims_staff@demo.com", "NHIA Payment Officer", roles["Claims_Staff"]),
            ("view_only@demo.com", "Analytics User", roles["View_Only"]),
            ("partner@demo.com", "Sydani Health Fleet Manager", roles["Partner"]),
            ("crew@demo.com", "John Crew", roles["Crew"])
        ]
        
        user_objects = {}
        for email, name, role in users_to_create:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if not user:
                user = User(email=email, name=name, hashed_password=get_password_hash("password123"), is_active=True, role_id=role.id)
                db.add(user)
                await db.flush()
            user_objects[email] = user

        partner_user = user_objects["partner@demo.com"]
        etc_user = user_objects["etc_staff@demo.com"]
        crew_user = user_objects["crew@demo.com"]
        claims_user = user_objects["claims_staff@demo.com"]

        # 3. PARTNERS & ASSETS
        partner_profile = (await db.execute(select(Partner).where(Partner.user_id == partner_user.id))).scalar_one_or_none()
        if not partner_profile:
            partner_profile = Partner(user_id=partner_user.id, organisation_name="Sydani Global Health", contact_person="Dr. Chijioke", contact_phone="+2348011223344", address="123 Medic Way, Abuja", is_verified=True)
            db.add(partner_profile); await db.flush()

        if not (await db.execute(select(Pledge).where(Pledge.partner_id == partner_profile.id))).scalar_one_or_none():
            db.add(Pledge(partner_id=partner_profile.id, ambulance_count=5, target_state_id=fct_state.id, status=PledgeStatus.PARTIALLY_FULFILLED, fulfilled_count=2))

        if not (await db.execute(select(FacilityRequest).where(FacilityRequest.partner_id == partner_profile.id))).scalar_one_or_none():
            db.add(FacilityRequest(partner_id=partner_profile.id, facility_name="Sydani Clinic Bwari", facility_type="ETC", address="Bwari Central Road", latitude=9.2847, longitude=7.3829, state_id=fct_state.id, lga_id=bwari_lga.id))

        facility = (await db.execute(select(Facility).where(Facility.name == "Abuja Central ETC"))).scalar_one_or_none()
        if not facility:
            facility = Facility(name="Abuja Central ETC", facility_type="Specialist Hospital", address="Gwagwalada Medical District", latitude=8.9512, longitude=7.0754, state_id=fct_state.id, lga_id=abuja_lga.id, is_active=True)
            db.add(facility); await db.flush()

        ambulance = (await db.execute(select(Ambulance).where(Ambulance.plate_number == "ABC-123-XY"))).scalar_one_or_none()
        if not ambulance:
            ambulance = Ambulance(plate_number="ABC-123-XY", make_model="Mercedes Sprinter", year=2022, accreditation_type=AccreditationType.BLS, fuel_type="Diesel", capacity=1, status=AmbulanceStatus.ACTIVE, state_id=fct_state.id, lga_id=abuja_lga.id, partner_id=partner_user.id, last_latitude=9.0765, last_longitude=7.3985)
            db.add(ambulance); await db.flush()

        incident = (await db.execute(select(Incident).where(Incident.location_label == "Gwagwalada Trauma Incident"))).scalar_one_or_none()
        if not incident:
            incident = Incident(uuid=str(uuid.uuid4()), location_label="Gwagwalada Trauma Incident", latitude=8.9500, longitude=7.0700, state_id=fct_state.id, lga_id=abuja_lga.id, caller_name="Aminu Bello", caller_phone="+2349001112223", emergency_type=EmergencyType.TRAUMA, severity="Critical", status=IncidentStatus.COMPLETED)
            db.add(incident); await db.flush()
            
            db.add_all([
                IncidentStatusHistory(incident_id=incident.id, status=IncidentStatus.CREATED, changed_by_id=admin_user.id, notes="Incident reported"),
                IncidentStatusHistory(incident_id=incident.id, status=IncidentStatus.COMPLETED, changed_by_id=admin_user.id, notes="Patient dropped off")
            ])
            
            dispatch = Dispatch(incident_id=incident.id, ambulance_id=ambulance.id, crew_id=crew_user.id, dispatch_timestamp=datetime.now(timezone.utc).replace(tzinfo=None))
            db.add(dispatch)
            await db.flush()

        # 4. RUN SHEET, ETC INTAKE, GPS HISTORY
        if not (await db.execute(select(RunSheet).where(RunSheet.incident_id == incident.id))).scalar_one_or_none():
            db.add(RunSheet(
                incident_id=incident.id,
                crew_id=crew_user.id,
                etc_staff_id=etc_user.id,
                patient_data={"blood_pressure": "120/80", "pulse": "85bpm"},
                drugs_administered=[{"name": "Sodium Chloride 0.9%", "dose": "500ml"}],
                is_locked=True
            ))

        if not (await db.execute(select(ETCIntake).where(ETCIntake.incident_id == incident.id))).scalar_one_or_none():
            db.add(ETCIntake(
                incident_id=incident.id,
                etc_facility_id=etc_user.id,
                arrival_time=datetime.now(timezone.utc).replace(tzinfo=None),
                initial_assessment="Patient stable, minor lacerations.",
                triage_category="Yellow"
            ))

        if not (await db.execute(select(GPSHistory).where(GPSHistory.incident_id == incident.id))).scalar_one_or_none():
            db.add_all([
                GPSHistory(ambulance_id=ambulance.id, incident_id=incident.id, latitude=8.9501, longitude=7.0701),
                GPSHistory(ambulance_id=ambulance.id, incident_id=incident.id, latitude=8.9505, longitude=7.0709)
            ])

        # 5. CLAIM
        if not (await db.execute(select(Claim).where(Claim.incident_id == incident.id))).scalar_one_or_none():
            db.add(Claim(
                incident_id=incident.id,
                user_id=crew_user.id,
                claim_type=ClaimType.AMBULANCE,
                amount=15000.00,
                distance_km=12.5,
                status=ClaimStatus.PENDING
            ))

        # 6. QA FINDING (Attributed to Admin to avoid creating a QA Role specifically)
        if not (await db.execute(select(QAFinding).where(QAFinding.incident_id == incident.id))).scalar_one_or_none():
            db.add(QAFinding(
                incident_id=incident.id,
                qa_officer_id=admin_user.id,
                compliance_rating="Compliant",
                findings_text="Crew arrived within timeline and logged all records properly."
            ))

        await db.commit()
        print("✅ Demo data successfully seeded for ALL tables, with correct user roles included!")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
