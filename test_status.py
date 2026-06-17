import asyncio
import asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://root:chibuike4u@localhost:5432/nemsas')
    amb = await conn.fetchval("SELECT count(*) FROM ambulances WHERE status IS NULL OR status != 'approved'")
    hosp = await conn.fetchval("SELECT count(*) FROM hospitals WHERE status IS NULL OR status != 'approved'")
    print(f"Ambulances to update: {amb}")
    print(f"Hospitals to update: {hosp}")
    
    # Check partner tables just in case
    p_amb = await conn.fetchval("SELECT count(*) FROM partner_ambulances WHERE status IS NULL OR status != 'approved'")
    p_hosp = await conn.fetchval("SELECT count(*) FROM partner_facilities WHERE status IS NULL OR status != 'approved'")
    print(f"Partner Ambulances to update: {p_amb}")
    print(f"Partner Facilities to update: {p_hosp}")

    await conn.close()
asyncio.run(main())
