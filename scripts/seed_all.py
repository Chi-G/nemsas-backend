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
        
    print("\n✅ All seeding operations completed!")

if __name__ == "__main__":
    asyncio.run(run_all_seeds())
