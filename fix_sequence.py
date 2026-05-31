import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as session:
        try:
            await session.execute(text("SELECT setval('claims_id_seq', COALESCE((SELECT MAX(id) FROM claims), 1));"))
            await session.commit()
            print("Successfully updated claims_id_seq")
        except Exception as e:
            print(f"Error updating claims_id_seq: {e}")
            
        try:
            await session.execute(text("SELECT setval('claim_images_id_seq', COALESCE((SELECT MAX(id) FROM claim_images), 1));"))
            await session.commit()
            print("Successfully updated claim_images_id_seq")
        except Exception as e:
            print(f"Error updating claim_images_id_seq: {e}")

        try:
            await session.execute(text("SELECT setval('incidents_id_seq', COALESCE((SELECT MAX(id) FROM incidents), 1));"))
            await session.commit()
            print("Successfully updated incidents_id_seq")
        except Exception as e:
            print(f"Error updating incidents_id_seq: {e}")

if __name__ == "__main__":
    asyncio.run(main())
