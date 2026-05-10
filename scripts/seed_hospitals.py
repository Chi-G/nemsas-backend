import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.hospital import Hospital

async def seed_hospitals():
    json_path = os.path.join(os.path.dirname(__file__), "hospitals.json")
    
    # Data from user request
    default_data = [
        {
            "id": 429,
            "name": "Annunciation Specialist Hospital",
            "hospitalTypeId": 1,
            "stateId": 14,
            "lgaId": 302,
            "location": "Annunciation Hospital Road in Emene",
            "address1": "27 Annunciation \nHospital Road, Emene, \nEnugu 400211, Enugu, ",
            "address2": "...",
            "landmark": "Emene Junction or near the Emenite area",
            "dateAdded": "2026-05-04T11:38:56.308474+00:00"
        },
        {
            "id": 428,
            "name": "DR. NLOGHA OKEKE MEMORIAL MEDICAL FOUNDATION/Eastern Nigeria Medical Centre",
            "hospitalTypeId": 1,
            "stateId": 14,
            "lgaId": 302,
            "location": "Uwani, Enugu,",
            "address1": "30 AMIGBO LANE, UWANI, \nENUGU ",
            "address2": "...",
            "landmark": "opposite CIC, Enugu ",
            "dateAdded": "2026-05-04T11:36:33.264426+00:00"
        },
        {
            "id": 427,
            "name": "POSH Specialist Hospital (Patrick Otiji Specialist Hospital)",
            "hospitalTypeId": 1,
            "stateId": 14,
            "lgaId": 303,
            "location": "New Haven",
            "address1": "100 Chime Avenue, \nNew Haven, Enugu,",
            "address2": "...",
            "landmark": "along the main Chime Avenue, near the New Haven/Independence Layout intersection area./ Opposite De Pines Bar ",
            "dateAdded": "2026-05-04T11:35:18.130679+00:00"
        }
    ]

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
    else:
        data = default_data
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

    async with SessionLocal() as session:
        print(f"🏥 Seeding {len(data)} Hospitals...")
        
        for item in data:
            try:
                async with session.begin_nested():
                    date_added = None
                    if item.get("dateAdded"):
                        try:
                            date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                        except:
                            date_added = datetime.now()

                    hospital_type_id = item.get("hospitalTypeId")
                    if hospital_type_id == 0:
                        hospital_type_id = None
                        
                    state_id = item.get("stateId")
                    if state_id == 0:
                        state_id = None
                        
                    lga_id = item.get("lgaId")
                    if lga_id == 0:
                        lga_id = None

                    stmt = insert(Hospital).values(
                        id=item["id"],
                        name=item["name"],
                        hospital_type_id=hospital_type_id,
                        state_id=state_id,
                        lga_id=lga_id,
                        location=item.get("location"),
                        address1=item.get("address1"),
                        address2=item.get("address2"),
                        landmark=item.get("landmark"),
                        date_added=date_added
                    ).on_conflict_do_update(
                        index_elements=['id'],
                        set_={
                            'name': item['name'],
                            'hospital_type_id': hospital_type_id,
                            'state_id': state_id,
                            'lga_id': lga_id,
                            'location': item.get('location'),
                            'address1': item.get('address1'),
                            'address2': item.get('address2'),
                            'landmark': item.get('landmark'),
                            'date_added': date_added
                        }
                    )
                    await session.execute(stmt)
            except Exception as e:
                print(f"⚠️ Skipping hospital ID {item['id']} due to error: {str(e)[:100]}...")
                continue
        
        await session.commit()
        print("✅ Hospitals seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_hospitals())
