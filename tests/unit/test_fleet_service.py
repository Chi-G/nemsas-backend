import pytest
from src.services.ambulance import ambulance_service
from src.db.models.ambulance import Ambulance, AccreditationType, AmbulanceStatus
from src.db.models.partner import Partner, Pledge, PledgeStatus
from src.schemas.ambulance import AmbulanceCreate
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
import uuid

@pytest.mark.asyncio
async def test_ambulance_registration_increments_pledge(db: AsyncSession):
    # Setup Partner and Pledge
    partner_user_id = 100 # Mock user id
    partner = Partner(user_id=partner_user_id, organisation_name="Test Partner", contact_person="John", contact_phone="123", address="ABC")
    db.add(partner)
    await db.flush()
    
    pledge = Pledge(partner_id=partner.id, ambulance_count=5, target_state_id=1, fulfilled_count=0, status=PledgeStatus.PENDING)
    db.add(pledge)
    await db.commit()
    
    # Register Ambulance
    amb_in = AmbulanceCreate(
        plate_number=f"TEST-{uuid.uuid4().hex[:5]}",
        make_model="Toyota",
        year=2020,
        accreditation_type=AccreditationType.BLS,
        state_id=1,
        lga_id=1,
        partner_id=partner_user_id
    )
    
    ambulance = await ambulance_service.create(db, obj_in=amb_in)
    
    # Verify Pledge increment
    await db.refresh(pledge)
    assert pledge.fulfilled_count == 1
    assert pledge.status == PledgeStatus.IN_PROGRESS

@pytest.mark.asyncio
async def test_bulk_validation_logic(db: AsyncSession):
    csv_content = (
        "plate_number,make_model,year,accreditation_type,state_id,lga_id\n"
        "VAL-001,Toyota Hiace,2022,BLS,1,1\n"
        ",Missing Plate,2022,ALS,1,1\n" # Invalid
    )
    
    report = await ambulance_service.bulk_validate_csv(db, csv_content=csv_content)
    assert report.total_rows == 2
    assert report.passed_rows == 1
    assert report.failed_rows == 1
    assert report.reports[1].is_valid is False
    assert "Plate number is required" in report.reports[1].errors
