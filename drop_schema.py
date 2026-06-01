import asyncio
from sqlalchemy import text
from app.db.session import engine

async def drop_all():
    async with engine.begin() as conn:
        print("Dropping schema public cascade...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        print("Done.")

if __name__ == "__main__":
    asyncio.run(drop_all())
