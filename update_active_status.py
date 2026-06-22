import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from app.core.config import settings

async def migrate_data():
    db_url = str(settings.DATABASE_URL)
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        # If status is pending, active_status is pending
        await conn.execute(text("UPDATE ambulances SET active_status = 'pending' WHERE status = 'pending' OR status = 'Pending'"))
        
        # If status is out of service, active_status is out of service, and status becomes approved
        await conn.execute(text("UPDATE ambulances SET active_status = 'out_of_service', status = 'approved' WHERE status ILIKE '%out of service%' OR status ILIKE '%out_of_service%'"))
        
        # If status is under maintenance, active_status is under maintenance, and status becomes approved
        await conn.execute(text("UPDATE ambulances SET active_status = 'under_maintenance', status = 'approved' WHERE status ILIKE '%under maintenance%' OR status ILIKE '%under_maintenance%' OR status ILIKE '%under_maintainance%'"))
        
        # For all other approved ones (or any others), make them active
        await conn.execute(text("UPDATE ambulances SET active_status = 'active', status = 'approved' WHERE status = 'approved' OR status = 'Approved' OR active_status IS NULL"))

        print("Migration complete!")
        
    await engine.dispose()

asyncio.run(migrate_data())
