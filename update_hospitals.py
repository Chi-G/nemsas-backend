import asyncio
from app.db.session import SessionLocal
from app.models.hospital import Hospital
from sqlalchemy import update

async def main():
    async with SessionLocal() as db:
        # We need raw SQL to alter the table first, then we update it.
        # SQLAlchemy `update()` only works if the columns exist, so we use execute text first.
        from sqlalchemy import text
        
        try:
            await db.execute(text("ALTER TABLE hospitals ADD COLUMN status VARCHAR DEFAULT 'approved'"))
        except Exception as e:
            print(f"Column status may already exist: {e}")
            
        try:
            await db.execute(text("ALTER TABLE hospitals ADD COLUMN added_by INTEGER REFERENCES partner_users(id)"))
        except Exception as e:
            print(f"Column added_by may already exist: {e}")
            
        await db.execute(text("UPDATE hospitals SET status = 'approved' WHERE status IS NULL"))
        await db.commit()
        print("Updated hospitals successfully")

if __name__ == "__main__":
    asyncio.run(main())
