import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def run():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT id, take_off_time, arrival_time, total_minutes_to_hospital, distance_covered FROM run_sheets ORDER BY id DESC LIMIT 5;"))
        for row in res.mappings().all():
            print(row)

asyncio.run(run())
