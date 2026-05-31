import asyncio
from app.db.session import SessionLocal
from app.crud.claim import claim as crud_claim
from app.schemas.claim import ClaimCreate
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        claim_in = ClaimCreate(title="Test Claim", patient_id=4791, incident_id=5154)
        
        # Manually create to test expunge
        obj_in_data = claim_in.model_dump()
        obj_in_data.pop("image_url", None)
        from app.models.claim import Claim
        db_obj = Claim(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        
        db.expunge(db_obj) # Expunge to force a fresh eager load
        
        stmt = select(Claim).options(*crud_claim._get_claim_options()).where(Claim.id == db_obj.id)
        result = await db.execute(stmt)
        item = result.scalars().first()
        
        try:
            print("Accessing incident")
            inc = item.incident
            print("Incident ID:", inc.id if inc else None)
            print("Accessing patient")
            pat = item.patient
            if pat:
                print("Accessing interventions")
                getattr(pat, 'interventions', None)
                print("Accessing etc_interventions")
                getattr(pat, 'etc_interventions', None)
            print("All accessed")
        except Exception as e:
            print("LAZY LOAD ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())
