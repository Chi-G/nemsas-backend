import asyncio
import calendar
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.getcwd())

from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.session import SessionLocal
from app.models.monitoring import Monitoring

SEED_YEAR = 2026

month_to_int = {name: i for i, name in enumerate(calendar.month_name) if i > 0}

data = [
    {"month": "January", "noOfTransport": 0, "noOfMamiiLGAs": 33, "byTricycleAmbulance": 102, "byNurtwDriver": 90, "bls": 103, "laborTransportation": 62, "obstetricTransportation": 48, "neonatalTransportation": 61, "bemonc": 102, "cemonc": 69, "maternalMortalities": 18, "neonatalMortalities": 8},
    {"month": "February", "noOfTransport": 0, "noOfMamiiLGAs": 39, "byTricycleAmbulance": 148, "byNurtwDriver": 145, "bls": 194, "laborTransportation": 44, "obstetricTransportation": 102, "neonatalTransportation": 154, "bemonc": 2443, "cemonc": 2331, "maternalMortalities": 6, "neonatalMortalities": 22},
    {"month": "March", "noOfTransport": 0, "noOfMamiiLGAs": 64, "byTricycleAmbulance": 77, "byNurtwDriver": 98, "bls": 161, "laborTransportation": 70, "obstetricTransportation": 99, "neonatalTransportation": 118, "bemonc": 117, "cemonc": 105, "maternalMortalities": 34, "neonatalMortalities": 135},
    {"month": "April", "noOfTransport": 0, "noOfMamiiLGAs": 67, "byTricycleAmbulance": 113, "byNurtwDriver": 83, "bls": 174, "laborTransportation": 119, "obstetricTransportation": 63, "neonatalTransportation": 157, "bemonc": 93, "cemonc": 163, "maternalMortalities": 25, "neonatalMortalities": 0},
    {"month": "May", "noOfTransport": 12, "noOfMamiiLGAs": 88, "byTricycleAmbulance": 141, "byNurtwDriver": 94, "bls": 140, "laborTransportation": 125, "obstetricTransportation": 155, "neonatalTransportation": 112, "bemonc": 127, "cemonc": 97, "maternalMortalities": 37, "neonatalMortalities": 19},
    {"month": "June", "noOfTransport": 0, "noOfMamiiLGAs": 60, "byTricycleAmbulance": 21, "byNurtwDriver": 105, "bls": 84, "laborTransportation": 48, "obstetricTransportation": 147, "neonatalTransportation": 117, "bemonc": 36, "cemonc": 54, "maternalMortalities": 24, "neonatalMortalities": 3},
    {"month": "July", "noOfTransport": 888, "noOfMamiiLGAs": 85, "byTricycleAmbulance": 47, "byNurtwDriver": 147, "bls": 216, "laborTransportation": 133, "obstetricTransportation": 120, "neonatalTransportation": 165, "bemonc": 186, "cemonc": 2047, "maternalMortalities": 30, "neonatalMortalities": 21},
    {"month": "August", "noOfTransport": 1100, "noOfMamiiLGAs": 99, "byTricycleAmbulance": 361, "byNurtwDriver": 310, "bls": 726, "laborTransportation": 554, "obstetricTransportation": 482, "neonatalTransportation": 316, "bemonc": 69, "cemonc": 1279, "maternalMortalities": 38, "neonatalMortalities": 10},
    {"month": "September", "noOfTransport": 100, "noOfMamiiLGAs": 33, "byTricycleAmbulance": 161, "byNurtwDriver": 134, "bls": 130, "laborTransportation": 203, "obstetricTransportation": 61, "neonatalTransportation": 154, "bemonc": 139, "cemonc": 271, "maternalMortalities": 26, "neonatalMortalities": 6},
    {"month": "October", "noOfTransport": 0, "noOfMamiiLGAs": 102, "byTricycleAmbulance": 227, "byNurtwDriver": 131, "bls": 209, "laborTransportation": 88, "obstetricTransportation": 208, "neonatalTransportation": 208, "bemonc": 151, "cemonc": 152, "maternalMortalities": 66, "neonatalMortalities": 60},
    {"month": "December", "noOfTransport": 535, "noOfMamiiLGAs": 5, "byTricycleAmbulance": 2, "byNurtwDriver": 224, "bls": 310, "laborTransportation": 527, "obstetricTransportation": 6, "neonatalTransportation": 2, "bemonc": 525, "cemonc": 9, "maternalMortalities": 0, "neonatalMortalities": 0},
]


async def seed():
    async with SessionLocal() as db:
        inserted = 0
        skipped = 0

        for item in data:
            month_int = month_to_int.get(str(item["month"]))
            if not month_int:
                continue

            record = {
                "year": SEED_YEAR,
                "month": month_int,
                "no_of_transport": item.get("noOfTransport", 0),
                "no_of_mamii_lgas": item.get("noOfMamiiLGAs", 0),
                "by_tricycle_ambulance": item.get("byTricycleAmbulance", 0),
                "by_nurtw_driver": item.get("byNurtwDriver", 0),
                "bls": item.get("bls", 0),
                "labor_transportation": item.get("laborTransportation", 0),
                "obstetric_transportation": item.get("obstetricTransportation", 0),
                "neonatal_transportation": item.get("neonatalTransportation", 0),
                "bemonc": item.get("bemonc", 0),
                "cemonc": item.get("cemonc", 0),
                "maternal_mortalities": item.get("maternalMortalities", 0),
                "neonatal_mortalities": item.get("neonatalMortalities", 0),
                "state_id": 1,
                "date_added": datetime.now(timezone.utc),
                "added_by": "System",
                "is_active": True,
            }

            # Idempotent upsert: skip if record already exists (by primary key)
            stmt = pg_insert(Monitoring).values(record).on_conflict_do_nothing()
            result = await db.execute(stmt)
            if result.rowcount:
                inserted += 1
            else:
                skipped += 1

        await db.commit()
        print(f"✅ Monitoring seeding complete: {inserted} inserted, {skipped} skipped (already existed).")


if __name__ == "__main__":
    asyncio.run(seed())
