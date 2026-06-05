import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def run():
    async with SessionLocal() as db:
        for table in ["partners", "pledges", "facility_requests"]:
            try:
                res = await db.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = res.scalar()
                print(f"Table '{table}' row count:", count)
                if count > 0:
                    res_rows = await db.execute(text(f"SELECT * FROM {table} LIMIT 5;"))
                    print(f"Sample rows from '{table}':")
                    for row in res_rows.mappings().all():
                        print(row)
            except Exception as e:
                print(f"Error querying '{table}': {e}")

asyncio.run(run())

