import json
import asyncio
import sys
import os

# Add the current directory to sys.path to import app modules
sys.path.append(os.getcwd())

from sqlalchemy import select, update
from app.db.session import SessionLocal
from app.models.incident import Incident

async def update_incident_state_ids(batch_size=1000):
    """
    Populates state_id in the incidents table based on state_name using scripts/states.json.
    Processes incidents in batches by state name.
    """
    # 1. Load states mapping from states.json
    states_file = "scripts/states.json"
    if not os.path.exists(states_file):
        print(f"Error: {states_file} not found.")
        return

    with open(states_file, "r") as f:
        states_data = json.load(f)

    # Create a normalized mapping: lowercase name (no spaces) -> ID
    state_map = {}
    for s in states_data:
        norm_name = s["name"].lower().replace(" ", "").strip()
        state_map[norm_name] = s["id"]
    
    # Add common variations if they aren't already there
    if "fct" in state_map and "fctabuja" not in state_map:
        state_map["fctabuja"] = state_map["fct"]
    if "akwaibom" in state_map:
        state_map["akwaibom"] = state_map["akwaibom"]

    print(f"Loaded {len(state_map)} state mappings from {states_file}")

    async with SessionLocal() as db:
        # 2. Get all unique state names that need processing
        stmt = select(Incident.state_name).where(Incident.state_id == None).distinct()
        result = await db.execute(stmt)
        unique_state_names = [row[0] for row in result.all() if row[0]]

        if not unique_state_names:
            print("No incidents found with missing state_id.")
            return

        print(f"Found {len(unique_state_names)} unique state names in incidents needing update.")

        # 3. Process each state name
        for state_name in unique_state_names:
            norm_name = state_name.lower().replace(" ", "").strip()
            target_id = state_map.get(norm_name)

            if target_id:
                print(f"Updating incidents for state: '{state_name}' -> state_id: {target_id}")
                
                # Perform update in batches for this state
                # Using a single UPDATE statement is most efficient
                update_stmt = (
                    update(Incident)
                    .where(Incident.state_name == state_name)
                    .where(Incident.state_id == None)
                    .values(state_id=target_id)
                )
                
                res = await db.execute(update_stmt)
                count = res.rowcount
                print(f"  Successfully updated {count} rows.")
                await db.commit()
            else:
                print(f"  Warning: No mapping found for state name: '{state_name}' (normalized: '{norm_name}')")

        print("\nAll processing complete.")

if __name__ == "__main__":
    asyncio.run(update_incident_state_ids())
