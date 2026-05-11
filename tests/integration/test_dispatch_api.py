import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.ambulance import Ambulance, AmbulanceStatus, Dispatch
from src.db.models.incident import Incident, IncidentStatus, EmergencyType
import uuid

@pytest.mark.asyncio
async def test_get_nearest_ambulances_with_fallback(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    # Setup: Create 2 ambulances at different locations
    amb1 = Ambulance(
        plate_number="AMB-001",
        make_model="Toyota Hiace",
        year=2022,
        accreditation_type="BLS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE,
        last_latitude=9.05,
        last_longitude=7.48
    )
    amb2 = Ambulance(
        plate_number="AMB-002",
        make_model="Toyota Hiace",
        year=2022,
        accreditation_type="ALS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE,
        last_latitude=9.10,
        last_longitude=7.55
    )
    db.add_all([amb1, amb2])
    await db.commit()

    # Query nearest to (9.06, 7.49)
    response = await client.get(
        "/api/v1/dispatch/nearest?lat=9.06&lon=7.49&limit=2",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # First one should be AMB-001 (closer to 9.06, 7.49 than 9.10, 7.55)
    assert data[0]["ambulance"]["plate_number"] == "AMB-001"
    assert "distance_meters" in data[0]

@pytest.mark.asyncio
async def test_assign_multiple_ambulances_notifications(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    # Setup
    incident = Incident(
        uuid=str(uuid.uuid4()),
        caller_name="Test",
        caller_phone="08012345678",
        emergency_type=EmergencyType.MEDICAL,
        location_label="Test Location",
        state_id=1,
        status=IncidentStatus.CREATED
    )
    db.add(incident)
    await db.flush()
    
    amb1 = Ambulance(
        plate_number="AMB-101",
        make_model="Toyota",
        year=2022,
        accreditation_type="BLS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE
    )
    amb2 = Ambulance(
        plate_number="AMB-102",
        make_model="Toyota",
        year=2022,
        accreditation_type="BLS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE
    )
    db.add_all([amb1, amb2])
    await db.commit()

    # Assign both
    response = await client.post(
        f"/api/v1/dispatch/assign?incident_id={incident.id}",
        json=[amb1.id, amb2.id],
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check ambulance statuses
    await db.refresh(amb1)
    await db.refresh(amb2)
    assert amb1.status == AmbulanceStatus.ON_DUTY
    assert amb2.status == AmbulanceStatus.ON_DUTY

@pytest.mark.asyncio
async def test_gps_tracking_distance_accumulation(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    # Setup
    amb = Ambulance(
        plate_number="DIST-TEST",
        make_model="Test",
        year=2022,
        accreditation_type="BLS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE,
        last_latitude=9.00,
        last_longitude=7.00
    )
    db.add(amb)
    await db.flush()
    
    incident = Incident(
        uuid=str(uuid.uuid4()),
        caller_name="Dist",
        caller_phone="080",
        emergency_type=EmergencyType.MEDICAL,
        location_label="Test",
        state_id=1,
        status=IncidentStatus.DISPATCHED
    )
    db.add(incident)
    await db.flush()
    
    dispatch = Dispatch(
        incident_id=incident.id,
        ambulance_id=amb.id,
        crew_id=1,
        total_distance=0.0
    )
    db.add(dispatch)
    await db.commit()

    # Move 1: (9.01, 7.01) - Approx 1.57 km
    gps_data = {
        "ambulance_id": amb.id,
        "incident_id": incident.id,
        "latitude": 9.01,
        "longitude": 7.01,
        "is_paused": False,
        "incident_leg": "dispatch_to_scene"
    }
    response = await client.post(
        f"/api/v1/ambulances/{amb.id}/gps",
        json=gps_data,
        headers=admin_token_headers
    )
    assert response.status_code == 200
    
    # Check distance
    await db.refresh(dispatch)
    assert dispatch.total_distance > 0
    first_dist = dispatch.total_distance
    
    # Move 2: (9.02, 7.02)
    gps_data["latitude"] = 9.02
    gps_data["longitude"] = 7.02
    await client.post(
        f"/api/v1/ambulances/{amb.id}/gps",
        json=gps_data,
        headers=admin_token_headers
    )
    
    await db.refresh(dispatch)
    assert dispatch.total_distance > first_dist
