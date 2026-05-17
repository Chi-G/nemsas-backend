import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.claim import Claim, ClaimImage
from app.models.incident import Incident

async def seed_claims_images():
    json_path = os.path.join(os.path.dirname(__file__), "claims_images.json")
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        print("🔍 Pre-fetching claim and incident IDs for relationship validation...")
        claims_res = await session.execute(select(Claim.id))
        existing_claims = set(claims_res.scalars().all())

        incidents_res = await session.execute(select(Incident.id))
        existing_incidents = set(incidents_res.scalars().all())

        print(f"💼 Preparing {len(data)} claim images...")
        to_insert = []
        for item in data:
            claim_id = item.get("claimId")
            if claim_id not in existing_claims:
                claim_id = None

            incident_id = item.get("incidentId")
            if incident_id not in existing_incidents:
                incident_id = None

            to_insert.append({
                "id": item["id"],
                "claim_id": claim_id,
                "claim_title": item.get("claimTitle"),
                "incident_id": incident_id,
                "image_url": item.get("imageUrl"),
                "is_etc": bool(item.get("isEtc", False))
            })

        print(f"🚀 Starting batch insertion of {len(to_insert)} claim images...")
        BATCH_SIZE = 500
        total_added = 0

        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            stmt = insert(ClaimImage).values(chunk)

            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in ClaimImage.__table__.columns
                if c.name not in ['id']
            }

            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=update_dict
            )

            try:
                await session.execute(stmt)
                await session.commit()
                total_added += len(chunk)
                print(f"✅ Claims Images Batch {i//BATCH_SIZE + 1} processed. ({total_added}/{len(to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Claims Images Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print("🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(ClaimImage).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping claim image ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")

        print(f"🏁 Done! Successfully seeded {total_added} claim images.")

if __name__ == "__main__":
    asyncio.run(seed_claims_images())
