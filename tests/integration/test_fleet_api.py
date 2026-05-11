import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.ambulance import Ambulance, AccreditationType, AmbulanceStatus
from src.db.models.partner import Facility
import uuid

@pytest.mark.asyncio
async def test_ambulance_allocation_to_facility(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Setup
    facility = Facility(name="Fleet Test Hospital", facility_type="General", address="123 Road", latitude=6.5, longitude=3.4, state_id=1, lga_id=1)
    db.add(facility)
    await db.flush()
    
    ambulance = Ambulance(
        plate_number=f"ALLOC-{uuid.uuid4().hex[:5]}",
        make_model="Toyota",
        year=2021,
        accreditation_type=AccreditationType.BLS,
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE
    )
    db.add(ambulance)
    await db.commit()
    await db.refresh(ambulance)

    # Allocate
    response = await client.post(
        f"/api/v1/ambulances/{ambulance.id}/allocate",
        json={"facility_id": facility.id},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["facility_id"] == facility.id

@pytest.mark.asyncio
async def test_ambulance_status_update(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Setup
    ambulance = Ambulance(
        plate_number=f"STAT-{uuid.uuid4().hex[:5]}",
        make_model="Toyota",
        year=2021,
        accreditation_type=AccreditationType.ALS,
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE
    )
    db.add(ambulance)
    await db.commit()
    await db.refresh(ambulance)

    # Update Status
    response = await client.patch(
        f"/api/v1/ambulances/{ambulance.id}/status",
        json="Under Maintenance", # JSON string for AmbulanceStatus enum
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Under Maintenance"

@pytest.mark.asyncio
async def test_search_ambulances_filtering(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Assume some ambulances exist
    response = await client.get("/api/v1/ambulances/?status=Active", headers=admin_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
