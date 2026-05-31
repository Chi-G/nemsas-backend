import asyncio
from app.db.session import SessionLocal
from app.crud.claim import claim as crud_claim
from app.schemas.claim import ClaimCreate

async def main():
    async with SessionLocal() as db:
        claim_in = ClaimCreate(title="Test Claim")
        item = await crud_claim.create(db, obj_in=claim_in)
        print("Created claim:", item.id)
        
        # Test serialization
        from app.schemas.claim import ClaimResponse
        
        # Manually construct Pydantic response to test map_nested
        try:
            resp = ClaimResponse(success=True, message="Test", data=item)
            print("Successfully serialized")
        except Exception as e:
            print("Error serializing:", type(e), str(e))

if __name__ == "__main__":
    asyncio.run(main())
