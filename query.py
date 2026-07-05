import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text

async def run():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT id, event_status_type FROM incidents WHERE id=5187"))
        for row in result:
            print(f"ID: {row[0]}, event_status_type: '{row[1]}'")

asyncio.run(run())
