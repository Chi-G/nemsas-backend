import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.ambulance import Ambulance

async def seed_ambulances():
    async with SessionLocal() as session:
        try:
            with open("scripts/ambulances.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print("❌ scripts/ambulances.json not found")
            return

        print(f"🚑 Seeding {len(data)} Ambulances...")
        
        for item in data:
            try:
                async with session.begin_nested():
                    date_added = None
                    if item.get("dateAdded"):
                        try:
                            date_added = datetime.fromisoformat(item["dateAdded"].replace("Z", "+00:00"))
                        except:
                            date_added = datetime.now()

                    ambulance_type_id = item.get("ambulanceTypeId")
                    if ambulance_type_id == 0:
                        ambulance_type_id = None
                        
                    state_id = item.get("stateId")
                    if state_id == 0:
                        state_id = None
                        
                    lga_id = item.get("lgaId")
                    if lga_id == 0:
                        lga_id = None

                    stmt = insert(Ambulance).values(
                        id=item["id"],
                        name=item["name"],
                        code=item["code"],
                        location=item.get("location"),
                        ambulance_type_id=ambulance_type_id,
                        state_id=state_id,
                        lga_id=lga_id,
                        ward_id=item.get("wardId"),
                        nhia_or_shia=item.get("nhiAorSHIA"),
                        service_type=item.get("serviceType"),
                        online=item.get("online", True),
                        driver_name=item.get("driverName"),
                        contact_number=item.get("contactNumber"),
                        state_name=item.get("stateName"),
                        event_status_type=item.get("eventStatusType"),
                        date_added=date_added
                    ).on_conflict_do_update(
                        index_elements=['id'],
                        set_={
                            'name': item['name'],
                            'code': item['code'],
                            'location': item.get('location'),
                            'ambulance_type_id': ambulance_type_id,
                            'state_id': state_id,
                            'lga_id': lga_id,
                            'ward_id': item.get('wardId'),
                            'nhia_or_shia': item.get('nhiAorSHIA'),
                            'service_type': item.get('serviceType'),
                            'online': item.get('online', True),
                            'driver_name': item.get('driverName'),
                            'contact_number': item.get('contactNumber'),
                            'state_name': item.get('stateName'),
                            'event_status_type': item.get('eventStatusType'),
                            'date_added': date_added
                        }
                    )

                    await session.execute(stmt)
            except Exception as e:
                print(f"⚠️ Skipping ambulance ID {item['id']} due to error: {str(e)[:100]}...")
                continue
        
        await session.commit()
        print("✅ Ambulances seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_ambulances())
