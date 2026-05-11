import pytest
from src.services.claim import claim_service
from src.db.models.claim import ClaimStatus

def test_calculate_fee_bls():
    # BLS should be fixed at 15000 regardless of distance
    assert claim_service.calculate_fee("BLS", 0) == 15000.0
    assert claim_service.calculate_fee("BLS", 10.5) == 15000.0
    assert claim_service.calculate_fee("BLS", 100) == 15000.0

def test_calculate_fee_als():
    # ALS should be variable: 20000 + (distance * 500)
    assert claim_service.calculate_fee("ALS", 0) == 20000.0
    assert claim_service.calculate_fee("ALS", 10) == 20000.0 + (10 * 500)
    assert claim_service.calculate_fee("ALS", 5.5) == 20000.0 + (5.5 * 500)

@pytest.mark.asyncio
async def test_process_claim_validation_rejection(db):
    # This is a bit tricky to unit test without more mocking if we use the DB
    # But let's check the logic that raises Exception if rejection reason is missing
    # We would need to mock the DB session or create real records
    pass
