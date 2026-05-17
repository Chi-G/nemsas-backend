import asyncio
import json
import os
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.fee_category import FeeCategory

async def seed_fee_categories():
    json_path = os.path.join(os.path.dirname(__file__), "fee_categories.json")
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        print(f"🏷️ Preparing {len(data)} Fee Categories...")
        
        to_insert = []
        for item in data:
            fee_data = {
                "id": item["id"],
                "code": item.get("code", ""),
                "description": item.get("description", ""),
                "is_medicine": bool(item.get("isMedicine", 0))
            }
            to_insert.append(fee_data)

        print(f"🚀 Starting batch insertion of {len(to_insert)} fee categories...")
        BATCH_SIZE = 100
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            stmt = insert(FeeCategory).values(chunk)
            
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in FeeCategory.__table__.columns
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
                print(f"✅ Batch {i//BATCH_SIZE + 1} processed. ({total_added}/{len(to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Batch {i//BATCH_SIZE + 1} failed: {str(e).splitlines()[0]}")
                print(f"🔄 Falling back to one-by-one for this batch...")
                for single_item in chunk:
                    try:
                        inner_stmt = insert(FeeCategory).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping fee category ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")
        
        print(f"🏁 Done! Successfully seeded {total_added} fee categories.")

if __name__ == "__main__":
    asyncio.run(seed_fee_categories())
