import asyncio
from app.db.session import SessionLocal
from app.crud.claim import claim as crud_claim
from app.schemas.claim import ClaimCreate

async def main():
    async with SessionLocal() as db:
        claim_in = ClaimCreate(title="Test Claim", patient_id=4791, incident_id=5154)
        item = await crud_claim.create(db, obj_in=claim_in)
        print("Created claim:", item.id)
        
        try:
            print("Accessing incident")
            inc = item.incident
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
