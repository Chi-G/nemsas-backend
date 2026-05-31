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
    {"month": "January", "noOfTransport": 0, "noOfMamiiLGAs": 33, "byTricycleAmbulance": 102, "byNurtwDriver": 90, "bls": 103, "laborTransportation": 62, "obstetricTransportation": 48, "neonatalTransportation": 61, "bemonc": 102, "cemonc": 69, "maternalMortalities": 18, "neonatalMortalities": 8, "remark": "Satisfactory"},
    {"month": "February", "noOfTransport": 0, "noOfMamiiLGAs": 39, "byTricycleAmbulance": 148, "byNurtwDriver": 145, "bls": 194, "laborTransportation": 44, "obstetricTransportation": 102, "neonatalTransportation": 154, "bemonc": 2443, "cemonc": 2331, "maternalMortalities": 6, "neonatalMortalities": 22, "remark": "Satisfactory"},
    {"month": "March", "noOfTransport": 0, "noOfMamiiLGAs": 64, "byTricycleAmbulance": 77, "byNurtwDriver": 98, "bls": 161, "laborTransportation": 70, "obstetricTransportation": 99, "neonatalTransportation": 118, "bemonc": 117, "cemonc": 105, "maternalMortalities": 34, "neonatalMortalities": 135, "remark": "Satisfactory"},
    {"month": "April", "noOfTransport": 0, "noOfMamiiLGAs": 67, "byTricycleAmbulance": 113, "byNurtwDriver": 83, "bls": 174, "laborTransportation": 119, "obstetricTransportation": 63, "neonatalTransportation": 157, "bemonc": 93, "cemonc": 163, "maternalMortalities": 25, "neonatalMortalities": 0, "remark": "Satisfactory"},
    {"month": "May", "noOfTransport": 12, "noOfMamiiLGAs": 88, "byTricycleAmbulance": 141, "byNurtwDriver": 94, "bls": 140, "laborTransportation": 125, "obstetricTransportation": 155, "neonatalTransportation": 112, "bemonc": 127, "cemonc": 97, "maternalMortalities": 37, "neonatalMortalities": 19, "remark": "Satisfactory"},
    {"month": "June", "noOfTransport": 0, "noOfMamiiLGAs": 60, "byTricycleAmbulance": 21, "byNurtwDriver": 105, "bls": 84, "laborTransportation": 48, "obstetricTransportation": 147, "neonatalTransportation": 117, "bemonc": 36, "cemonc": 54, "maternalMortalities": 24, "neonatalMortalities": 3, "remark": "Satisfactory"},
    {"month": "July", "noOfTransport": 888, "noOfMamiiLGAs": 85, "byTricycleAmbulance": 47, "byNurtwDriver": 147, "bls": 216, "laborTransportation": 133, "obstetricTransportation": 120, "neonatalTransportation": 165, "bemonc": 186, "cemonc": 2047, "maternalMortalities": 30, "neonatalMortalities": 21, "remark": "Satisfactory"},
    {"month": "August", "noOfTransport": 1100, "noOfMamiiLGAs": 99, "byTricycleAmbulance": 361, "byNurtwDriver": 310, "bls": 726, "laborTransportation": 554, "obstetricTransportation": 482, "neonatalTransportation": 316, "bemonc": 69, "cemonc": 1279, "maternalMortalities": 38, "neonatalMortalities": 10, "remark": "Satisfactory"},
    {"month": "September", "noOfTransport": 100, "noOfMamiiLGAs": 33, "byTricycleAmbulance": 161, "byNurtwDriver": 134, "bls": 130, "laborTransportation": 203, "obstetricTransportation": 61, "neonatalTransportation": 154, "bemonc": 139, "cemonc": 271, "maternalMortalities": 26, "neonatalMortalities": 6, "remark": "Satisfactory"},
    {"month": "October", "noOfTransport": 0, "noOfMamiiLGAs": 102, "byTricycleAmbulance": 227, "byNurtwDriver": 131, "bls": 209, "laborTransportation": 88, "obstetricTransportation": 208, "neonatalTransportation": 208, "bemonc": 151, "cemonc": 152, "maternalMortalities": 66, "neonatalMortalities": 60, "remark": "Satisfactory"},
    {"month": "December", "noOfTransport": 535, "noOfMamiiLGAs": 5, "byTricycleAmbulance": 2, "byNurtwDriver": 224, "bls": 310, "laborTransportation": 527, "obstetricTransportation": 6, "neonatalTransportation": 2, "bemonc": 525, "cemonc": 9, "maternalMortalities": 0, "neonatalMortalities": 0, "remark": "Satisfactory"},
]


async def seed():
    async with SessionLocal() as db:
        inserted = 0
        updated = 0

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
                "remark": item.get("remark"),
                "state_id": 1,
                "date_added": datetime.now(timezone.utc),
                "added_by": "System",
                "is_active": True,
            }

            from sqlalchemy import select
            existing = await db.execute(
                select(Monitoring).where(
                    Monitoring.year == SEED_YEAR,
                    Monitoring.month == month_int,
                    Monitoring.state_id == 1
                )
            )
            existing_obj = existing.scalars().first()
            if existing_obj:
                existing_obj.no_of_transport = record["no_of_transport"]
                existing_obj.no_of_mamii_lgas = record["no_of_mamii_lgas"]
                existing_obj.by_tricycle_ambulance = record["by_tricycle_ambulance"]
                existing_obj.by_nurtw_driver = record["by_nurtw_driver"]
                existing_obj.bls = record["bls"]
                existing_obj.labor_transportation = record["labor_transportation"]
                existing_obj.obstetric_transportation = record["obstetric_transportation"]
                existing_obj.neonatal_transportation = record["neonatal_transportation"]
                existing_obj.bemonc = record["bemonc"]
                existing_obj.cemonc = record["cemonc"]
                existing_obj.maternal_mortalities = record["maternal_mortalities"]
                existing_obj.neonatal_mortalities = record["neonatal_mortalities"]
                existing_obj.remark = record["remark"]
                existing_obj.updated_at = datetime.now(timezone.utc)
                existing_obj.updated_by = "System"
                updated += 1
            else:
                db_obj = Monitoring(**record)
                db.add(db_obj)
                inserted += 1

        await db.commit()
        print(f"✅ Monitoring seeding complete: {inserted} inserted, {updated} updated (existing updated).")


if __name__ == "__main__":
    asyncio.run(seed())
