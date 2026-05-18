import asyncio
import json
import os
import sys
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert

# Ensure backend root is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.service import Service

async def seed_services():
    json_path = os.path.join(os.path.dirname(__file__), "services.json")
    if not os.path.exists(json_path):
        print(f"❌ {json_path} not found")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    async with SessionLocal() as session:
        print(f"💼 Preparing {len(data)} Services...")
        
        to_insert = []
        for item in data:
            date_added_val = None
            date_str = item.get("dateAdded")
            if date_str:
                try:
                    date_added_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            service_data = {
                "id": item["id"],
                "code": item.get("code", ""),
                "description": item.get("description", ""),
                "price": float(item.get("price", 0.0)),
                "fee_category_id": item.get("feeCategoryId"),
                "date_added": date_added_val
            }
            to_insert.append(service_data)

        print(f"🚀 Starting batch insertion of {len(to_insert)} services...")
        BATCH_SIZE = 500
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            stmt = insert(Service).values(chunk)
            
            update_dict = {
                c.name: stmt.excluded[c.name]
                for c in Service.__table__.columns
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
                        inner_stmt = insert(Service).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping service ID {single_item.get('id')}: {str(inner_e).splitlines()[0]}")
        
        print(f"🏁 Done! Successfully seeded {total_added} services.")

if __name__ == "__main__":
    asyncio.run(seed_services())
