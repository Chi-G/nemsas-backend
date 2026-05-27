import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
import uuid

from app.models.state import State
from app.models.incident import Incident
from app.models.claim import Claim, ClaimStatus, ClaimType
from app.models.user import User
from app.core.security import get_password_hash

@pytest_asyncio.fixture
async def setup_mobile_dashboard_data(db: AsyncSession):
    await db.execute(delete(Claim))
    await db.execute(delete(Incident))
    await db.execute(delete(User).where(User.email != "admin@test.com"))
    await db.commit()

    state_1 = await db.get(State, 1)
    if not state_1:
        state_1 = State(id=1, name="Abia", code="")
        db.add(state_1)

    await db.flush()

    ambulance_user = User(
        id=uuid.uuid4(),
        email="ambulance1@test.com",
        first_name="Ambulance",
        last_name="User",
        user_name="ambuser",
        hashed_password=get_password_hash("password123"),
        user_type="AMBULANCEUSER",
        state_id=1,
        ambulance_id=1,
        is_active=True
    )
    db.add(ambulance_user)
    await db.flush()

    # 3 Incidents for ambulance 1
    inc1 = Incident(serial_no="AB-001", description="Inc 1", incident_status_type="Reported", state_id=1, ambulance_id=1, date_added=datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc))
    inc2 = Incident(serial_no="AB-002", description="Inc 2", incident_status_type="Dispatched", state_id=1, ambulance_id=1, date_added=datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc))
    inc3 = Incident(serial_no="AB-003", description="Inc 3", incident_status_type="Completed", state_id=1, ambulance_id=1, date_added=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc))
    db.add_all([inc1, inc2, inc3])
    await db.flush()

    # 2 Claims for ambulance 1 (via incidents)
    claim1 = Claim(incident_id=inc1.id, user_id=ambulance_user.id, title="Cl 1", patient_name="Pat 1", claim_type=ClaimType.AMBULANCE, amount=10000.0, status=ClaimStatus.PENDING, created_at=datetime(2026, 5, 24, 10, 0, 0, tzinfo=timezone.utc))
    claim2 = Claim(incident_id=inc2.id, user_id=ambulance_user.id, title="Cl 2", patient_name="Pat 2", claim_type=ClaimType.ETC, amount=5000.0, status=ClaimStatus.APPROVED, created_at=datetime(2026, 5, 25, 10, 0, 0, tzinfo=timezone.utc))
    db.add_all([claim1, claim2])
    await db.commit()

    return ambulance_user

@pytest.mark.asyncio
async def test_superadmin_gets_empty_mobile_dashboard(client: AsyncClient, setup_mobile_dashboard_data, admin_token_headers):
    # Superadmin has no ambulance_id, should get empty data safely
    response = await client.get("/api/v1/dashboard/mobile", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["claimsOverview"]["total"] == 0
    assert data["incidentsOverview"]["total"] == 0
    assert len(data["recentActivity"]) == 0

@pytest.mark.asyncio
async def test_ambulance_user_mobile_dashboard(client: AsyncClient, setup_mobile_dashboard_data, get_user_token_headers):
    amb_user = setup_mobile_dashboard_data
    headers = get_user_token_headers(amb_user)

    response = await client.get("/api/v1/dashboard/mobile", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]

    # Ambulance 1 has 2 claims and 3 incidents
    assert data["claimsOverview"]["total"] == 2
    assert data["incidentsOverview"]["total"] == 3
    assert len(data["recentActivity"]) == 5 # 8 items max
    assert data["pagination"]["total"] == 5

@pytest.mark.asyncio
async def test_ambulance_user_mobile_activities_pagination(client: AsyncClient, setup_mobile_dashboard_data, get_user_token_headers):
    amb_user = setup_mobile_dashboard_data
    headers = get_user_token_headers(amb_user)

    # Test pagination on new activities endpoint (skip=2, limit=2)
    response = await client.get("/api/v1/dashboard/mobile/activities?skip=2&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]

    # Should only return recentActivity and pagination (no overviews)
    assert "claimsOverview" not in data
    assert "incidentsOverview" not in data
    assert len(data["recentActivity"]) == 2
    assert data["pagination"]["total"] == 5

@pytest.mark.asyncio
async def test_legacy_post_dashboard_mobile_empty(client: AsyncClient, setup_mobile_dashboard_data, admin_token_headers):
    response = await client.post("/api/v1/dashboard/dashboardMobile", json={"id": 1}, headers=admin_token_headers)
    assert response.status_code == 200
    # Even if they pass id: 1 in body, it's ignored now. Superadmin gets 0.
    data = response.json()["data"]
    assert data["claimsOverview"]["total"] == 0
