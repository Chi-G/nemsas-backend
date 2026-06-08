import asyncio
from app.db.session import SessionLocal
from app.crud.service import service_crud
from app.schemas.service import Service
from app.schemas.common import ResponseBase
from typing import List

async def test():
    async with SessionLocal() as db:
        services = await service_crud.get_all_services(db)
        
        # Manually validate against Pydantic schema
        try:
            services_data = [Service.model_validate(s) for s in services]
            res = ResponseBase[List[Service]](data=services_data, success=True, message="Success")
            print("Validation successful!")
        except Exception as e:
            print("Validation failed:")
            print(e)

asyncio.run(test())
