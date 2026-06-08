import asyncio
from app.db.session import SessionLocal
from app.crud.service import service_crud

async def test():
    async with SessionLocal() as db:
        services = await service_crud.get_all_services(db)
        for s in services:
            print(s.id, s.description, s.fee_category)
            break
        print("Success")

asyncio.run(test())
