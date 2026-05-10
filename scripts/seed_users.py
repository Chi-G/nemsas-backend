import asyncio
import json
import os
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

DEFAULT_PASSWORD = "NemsasDefault"
BATCH_SIZE = 500

def is_valid_uuid(val):
    if not val: return False
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def parse_date(date_str):
    if not date_str: return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None

async def seed_users():
    json_path = os.path.join(os.path.dirname(__file__), "users.json")
    if not os.path.exists(json_path):
        print(f"⚠️ Skipping Users: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        users_data = json.load(f)

    async with SessionLocal() as session:
        print(f"🧐 Validating and cleaning {len(users_data)} users...")
        hashed_pwd = get_password_hash(DEFAULT_PASSWORD)
        
        seen_emails = set()
        seen_usernames = set()
        seen_ids = set()
        to_insert = []
        
        for item in users_data:
            if not isinstance(item, dict): continue
            
            user_id = item.get("id")
            email = item.get("email")
            user_name = item.get("userName") or item.get("user_name") or f"user_{str(user_id)[:8]}"
            
            if not is_valid_uuid(user_id): continue
            
            if not email or email in seen_emails or user_id in seen_ids or user_name in seen_usernames:
                continue
            
            seen_emails.add(email)
            seen_ids.add(user_id)
            seen_usernames.add(user_name)
            
            # Helper to get values from multiple possible key names
            def get_val(item, *keys):
                for k in keys:
                    if k in item: return item[k]
                return None

            to_insert.append({
                "id": user_id,
                "first_name": get_val(item, "firstName", "first_name") or "Unknown",
                "middle_name": get_val(item, "middleName", "middle_name"),
                "last_name": get_val(item, "lastName", "last_name") or "Unknown",
                "user_name": user_name,
                "email": email,
                "phone_number": get_val(item, "phoneNumber", "phone_number"),
                "hashed_password": hashed_pwd,
                "sex": item.get("sex", 1),
                "is_active": True,
                "user_type": get_val(item, "userType", "user_type"),
                "organisation_name": get_val(item, "organisationName", "organisation_name"),
                "supervisor_user_id": str(get_val(item, "supervisorUserId", "supervisor_user_id") or ""),
                "emergency_treatment_center_id": get_val(item, "emergencyTreatmentCenterId", "emergency_treatment_center_id"),
                "ambulance_id": get_val(item, "ambulanceId", "ambulance_id"),
                "state_id": get_val(item, "state_Id", "stateId", "state_id"),
                "lga_id": get_val(item, "lga_Id", "lgaId", "lga_id"),
                "ward_id": get_val(item, "ward_Id", "wardId", "ward_id"),
                "date_joined": parse_date(get_val(item, "dateJoined", "date_joined"))
            })

        print(f"🚀 Starting insertion of {len(to_insert)} unique users...")
        total_added = 0
        
        for i in range(0, len(to_insert), BATCH_SIZE):
            chunk = to_insert[i:i + BATCH_SIZE]
            
            # Use PostgreSQL UPSERT to update existing records if needed, or just insert new ones
            # Actually ON CONFLICT DO UPDATE would be better to fix existing empty fields
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(User).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    "state_id": stmt.excluded.state_id,
                    "lga_id": stmt.excluded.lga_id,
                    "ward_id": stmt.excluded.ward_id,
                    "ambulance_id": stmt.excluded.ambulance_id,
                    "emergency_treatment_center_id": stmt.excluded.emergency_treatment_center_id,
                    "organisation_name": stmt.excluded.organisation_name
                }
            )
            
            try:
                await session.execute(stmt)
                await session.commit()
                total_added += len(chunk)
                print(f"✅ Chunk {i//BATCH_SIZE + 1} processed. ({total_added}/{len(to_insert)})")
            except Exception as e:
                await session.rollback()
                print(f"⚠️ Chunk {i//BATCH_SIZE + 1} failed. Falling back to one-by-one...")
                for single_item in chunk:
                    try:
                        inner_stmt = pg_insert(User).values(single_item)
                        inner_stmt = inner_stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_={k: v for k, v in single_item.items() if k != 'id'}
                        )
                        await session.execute(inner_stmt)
                        await session.commit()
                        total_added += 1
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"❌ Skipping {single_item['email']}: {str(inner_e).split('\n')[0]}")
        
        print(f"🏁 Done! Successfully processed {total_added} users.")

if __name__ == "__main__":
    asyncio.run(seed_users())
