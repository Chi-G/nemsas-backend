import asyncio
import os
import sys

# Ensure the app directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.seed_states import seed_states
from scripts.seed_lgas import seed_lgas
from scripts.seed_wards import seed_wards_from_file
from scripts.seed_roles import seed_roles
from scripts.seed_users import seed_users
from scripts.seed_hospital_types import seed_hospital_types
from scripts.seed_ambulance_types import seed_ambulance_types
from scripts.seed_hospitals import seed_hospitals
from scripts.seed_ambulances import seed_ambulances
from scripts.seed_incident_types import seed_incident_types
from scripts.seed_incidents import seed_incidents
from scripts.seed_patients import seed_patients
from scripts.seed_fee_categories import seed_fee_categories
from scripts.seed_services import seed_services



async def run_all_seeds():
    print("🚀 Starting master seeding process...")
    
    # 1. Base Data
    print("\n--- Seeding Roles ---")
    await seed_roles()

    print("\n--- Seeding States ---")
    await seed_states()
    
    print("\n--- Seeding LGAs ---")
    await seed_lgas()
    
    print("\n--- Seeding Wards (Batch) ---")
    ward_json_path = os.path.join(os.path.dirname(__file__), "wards.json")
    if os.path.exists(ward_json_path):
        await seed_wards_from_file(ward_json_path)
    else:
        print(f"⚠️ Warning: {ward_json_path} not found. Skipping wards.")

    # 2. Reference Types
    print("\n--- Seeding Hospital Types ---")
    await seed_hospital_types()

    print("\n--- Seeding Ambulance Types ---")
    await seed_ambulance_types()

    print("\n--- Seeding Incident Types ---")
    await seed_incident_types()

    print("\n--- Seeding Fee Categories ---")
    await seed_fee_categories()

    print("\n--- Seeding Services ---")
    await seed_services()



    # 3. Main Entities
    print("\n--- Seeding Hospitals ---")
    await seed_hospitals()

    print("\n--- Seeding Ambulances ---")
    await seed_ambulances()
    
    # 4. Users
    print("\n--- Seeding Users (with password hashing) ---")
    await seed_users()

    # 5. Operational Data
    print("\n--- Seeding Incidents ---")
    await seed_incidents()

    print("\n--- Seeding Patients ---")
    await seed_patients()

    print("\n--- Seeding Medical Interventions ---")
    from scripts.seed_medical_interventions import seed_medical_interventions
    await seed_medical_interventions()

    print("\n--- Seeding Claims and ETC Interventions ---")
    from scripts.seed_claims import seed_claims
    await seed_claims()

    print("\n--- Seeding Claim Images ---")
    from scripts.seed_claims_images import seed_claims_images
    await seed_claims_images()

    print("\n--- Synchronizing Database Sequences ---")
    from sqlalchemy import text
    from app.db.session import SessionLocal
    tables_to_sync = ['claims', 'hospitals', 'ambulances', 'patients', 'incidents', 'medical_interventions']
    async with SessionLocal() as session:
        for t in tables_to_sync:
            try:
                res = await session.execute(text(f"SELECT pg_get_serial_sequence('{t}', 'id');"))
                seq_name = res.scalar()
                if seq_name:
                    await session.execute(text(f"SELECT setval('{seq_name}', COALESCE(MAX(id), 1)) FROM {t};"))
                    print(f"✅ Sequence synchronized for: {t}")
            except Exception as e:
                print(f"⚠️ Failed to sync sequence for {t}: {str(e).splitlines()[0]}")
        await session.commit()
        
    print("\n✅ All seeding operations completed!")


if __name__ == "__main__":
    asyncio.run(run_all_seeds())

