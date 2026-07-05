import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE incident_types SET is_active = true WHERE is_active IS NULL"))
    await engine.dispose()
    print("Updated is_active to true for existing incident types")

if __name__ == "__main__":
    asyncio.run(main())
