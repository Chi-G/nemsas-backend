import asyncio
import json
import os
from sqlalchemy.future import select
from app.db.session import SessionLocal
from app.models.state import State

async def seed_states():
    json_path = os.path.join(os.path.dirname(__file__), "states.json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            states_data = json.load(f)
        print(f"Reading {len(states_data)} states from JSON file...")
    else:
        # Fallback to embedded data if JSON doesn't exist
        print("⚠️ states.json not found, using embedded fallback data.")
        states_data = [
            {"id": 1, "name": "Abia"},
            {"id": 2, "name": "Adamawa"},
            {"id": 3, "name": "Akwaibom"},
            {"id": 4, "name": "Anambra"},
            {"id": 5, "name": "Bauchi"},
            {"id": 6, "name": "Bayelsa"},
            {"id": 7, "name": "Benue"},
            {"id": 8, "name": "Borno"},
            {"id": 9, "name": "Cross River"},
            {"id": 10, "name": "Delta"},
            {"id": 11, "name": "Ebonyi"},
            {"id": 12, "name": "Edo"},
            {"id": 13, "name": "Ekiti"},
            {"id": 14, "name": "Enugu"},
            {"id": 15, "name": "Fct"},
            {"id": 16, "name": "Gombe"},
            {"id": 17, "name": "Imo"},
            {"id": 18, "name": "Jigawa"},
            {"id": 19, "name": "Kaduna"},
            {"id": 20, "name": "Kano"},
            {"id": 21, "name": "Katsina"},
            {"id": 22, "name": "Kebbi"},
            {"id": 23, "name": "Kogi"},
            {"id": 24, "name": "Kwara"},
            {"id": 25, "name": "Lagos"},
            {"id": 26, "name": "Nasarawa"},
            {"id": 27, "name": "Niger"},
            {"id": 28, "name": "Ogun"},
            {"id": 29, "name": "Ondo"},
            {"id": 30, "name": "Osun"},
            {"id": 31, "name": "Oyo"},
            {"id": 32, "name": "Plateau"},
            {"id": 33, "name": "Rivers"},
            {"id": 34, "name": "Sokoto"},
            {"id": 35, "name": "Taraba"},
            {"id": 36, "name": "Yobe"},
            {"id": 37, "name": "Zamfara"},
        ]

    async with SessionLocal() as session:
        for state_data in states_data:
            result = await session.execute(select(State).filter(State.id == state_data["id"]))
            existing_state = result.scalars().first()
            
            if not existing_state:
                new_state = State(
                    id=state_data["id"],
                    name=state_data["name"],
                    code=state_data.get("code", "")
                )
                session.add(new_state)
                print(f"Adding state: {state_data['name']}")
            else:
                print(f"State {state_data['name']} already exists, skipping.")
        
        await session.commit()
        print("State Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_states())
