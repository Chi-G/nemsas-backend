import asyncio
from app.db.session import SessionLocal
from app.crud.claim import claim as crud_claim
from app.schemas.claim import ClaimCreate

async def main():
    async with SessionLocal() as db:
        # Assuming patient 4791 exists from earlier error
        claim_in = ClaimCreate(title="Test Claim", patient_id=4791, incident_id=5154)
        item = await crud_claim.create(db, obj_in=claim_in)
        print("Created claim:", item.id)
        
        # Test serialization
        from app.schemas.claim import ClaimResponse
        
        # Manually construct Pydantic response to test map_nested
        try:
            resp = ClaimResponse.model_validate(
                {"success": True, "message": "Test", "data": item}
            )
            print("Successfully serialized")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
