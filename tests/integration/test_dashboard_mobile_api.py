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
    # Clean up existing tables to ensure a clean state
    await db.execute(delete(Claim))
    await db.execute(delete(Incident))
    await db.execute(delete(User).where(User.email != "admin@test.com"))
    await db.commit()

    # Seed states if they don't exist
    state_1 = await db.get(State, 1)
    if not state_1:
        state_1 = State(id=1, name="Abia", code="")
        db.add(state_1)

    state_8 = await db.get(State, 8)
    if not state_8:
        state_8 = State(id=8, name="Borno", code="")
        db.add(state_8)

    await db.flush()

    # Seed an admin user for state 1 (Abia)
    semsas_user = User(
        id=uuid.uuid4(),
        email="semsas@test.com",
        first_name="Semsas",
        last_name="User",
        user_name="semsasuser",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASADMIN",
        state_id=1,
        is_active=True
    )
    db.add(semsas_user)
    await db.flush()

    # Seed 3 Incidents for ambulance 1
    inc1 = Incident(
        serial_no="AB-001",
        description="First incident in Abia",
        incident_status_type="Reported",
        state_id=1,
        ambulance_id=1,
        date_added=datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
    )
    inc2 = Incident(
        serial_no="AB-002",
        description="Second incident in Abia",
        incident_status_type="Dispatched",
        state_id=1,
        ambulance_id=1,
        date_added=datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    )
    inc3 = Incident(
        serial_no="AB-003",
        description="Third incident in Abia",
        incident_status_type="Completed",
        state_id=1,
        ambulance_id=1,
        date_added=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc)
    )
    db.add_all([inc1, inc2, inc3])
    await db.flush()

    # Seed 1 Incident for ambulance 8
    inc_borno = Incident(
        serial_no="BO-001",
        description="Incident in Borno",
        incident_status_type="Reported",
        state_id=8,
        ambulance_id=8,
        date_added=datetime(2026, 5, 23, 10, 0, 0, tzinfo=timezone.utc)
    )
    db.add(inc_borno)
    await db.flush()

    # Seed 2 Claims in Abia (state_id=1)
    claim1 = Claim(
        incident_id=inc1.id,
        user_id=semsas_user.id,
        title="Ambulance claim 1",
        patient_name="Patient Abia 1",
        claim_type=ClaimType.AMBULANCE,
        amount=10000.0,
        status=ClaimStatus.PENDING,
        created_at=datetime(2026, 5, 24, 10, 0, 0, tzinfo=timezone.utc)
    )
    claim2 = Claim(
        incident_id=inc2.id,
        user_id=semsas_user.id,
        title="ETC claim 2",
        patient_name="Patient Abia 2",
        claim_type=ClaimType.ETC,
        amount=5000.0,
        status=ClaimStatus.APPROVED,
        created_at=datetime(2026, 5, 25, 10, 0, 0, tzinfo=timezone.utc)
    )
    db.add_all([claim1, claim2])
    await db.flush()

    # Seed 1 Claim in Borno (state_id=8)
    claim_borno = Claim(
        incident_id=inc_borno.id,
        user_id=semsas_user.id,
        title="Borno claim",
        patient_name="Patient Borno",
        claim_type=ClaimType.AMBULANCE,
        amount=8000.0,
        status=ClaimStatus.REJECTED,
        created_at=datetime(2026, 5, 26, 10, 0, 0, tzinfo=timezone.utc)
    )
    db.add(claim_borno)
    await db.commit()

    return semsas_user

@pytest.mark.asyncio
async def test_superadmin_mobile_dashboard_global(client: AsyncClient, setup_mobile_dashboard_data, admin_token_headers):
    # Call without state filter as superadmin (should see global stats and activities)
    # Total activities: 4 incidents + 3 claims = 7
    response = await client.get("/api/v1/dashboard/mobile?limit=10&skip=0", headers=admin_token_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    
    data = payload["data"]
    
    # Claims Overview:
    # Pending: 1, Approved: 1, Rejected: 1, Paid: 0, Total: 3
    claims_ov = data["claimsOverview"]
    assert claims_ov["pending"] == 1
    assert claims_ov["approved"] == 1
    assert claims_ov["rejected"] == 1
    assert claims_ov["total"] == 3

    # Incidents Overview:
    # Reported: 2, Dispatched: 1, Completed: 1, Total: 4
    inc_ov = data["incidentsOverview"]
    assert inc_ov["reported"] == 2
    assert inc_ov["dispatched"] == 1
    assert inc_ov["completed"] == 1
    assert inc_ov["total"] == 4

    # Recent Activity: Total count is 7
    activities = data["recentActivity"]
    pagination = data["pagination"]
    assert pagination["total"] == 7
    assert len(activities) == 7

    # Sorted descending by date. Top most activity should be the claim in Borno (May 26)
    assert activities[0]["title"].endswith("rejected")
    assert activities[0]["metaData"]["type"] == "claim"
    assert "meta-data" in activities[0]
    
    # Second should be ETC claim 2 (May 25)
    assert activities[1]["title"].endswith("approved")
    
    # Verify pagination works: skip=2, limit=2
    response_pag = await client.get("/api/v1/dashboard/mobile?limit=2&skip=2", headers=admin_token_headers)
    assert response_pag.status_code == 200
    payload_pag = response_pag.json()
    activities_pag = payload_pag["data"]["recentActivity"]
    assert len(activities_pag) == 2
    assert payload_pag["data"]["pagination"]["total"] == 7

@pytest.mark.asyncio
async def test_superadmin_mobile_dashboard_filtered(client: AsyncClient, setup_mobile_dashboard_data, admin_token_headers):
    # Filter by ambulanceId 1
    # Total ambulance 1: 3 Incidents, 2 Claims = 5 activities
    response = await client.get("/api/v1/dashboard/mobile?ambulanceId=1&limit=10&skip=0", headers=admin_token_headers)
    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    # Claims Overview: Pending: 1, Approved: 1, Rejected: 0, Total: 2
    claims_ov = data["claimsOverview"]
    assert claims_ov["pending"] == 1
    assert claims_ov["approved"] == 1
    assert claims_ov["rejected"] == 0
    assert claims_ov["total"] == 2

    # Incidents Overview: Reported: 1, Dispatched: 1, Completed: 1, Total: 3
    inc_ov = data["incidentsOverview"]
    assert inc_ov["reported"] == 1
    assert inc_ov["dispatched"] == 1
    assert inc_ov["completed"] == 1
    assert inc_ov["total"] == 3

    assert data["pagination"]["total"] == 5
    assert len(data["recentActivity"]) == 5

@pytest.mark.asyncio
async def test_semsas_user_mobile_dashboard_scoping(client: AsyncClient, setup_mobile_dashboard_data, get_user_token_headers):
    semsas_user = setup_mobile_dashboard_data
    headers = get_user_token_headers(semsas_user)

    # Call as semsas user, provide ambulanceId 1
    response = await client.get("/api/v1/dashboard/mobile?ambulanceId=1&limit=10&skip=0", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    # Verify same counts as ambulance 1
    assert data["claimsOverview"]["total"] == 2
    assert data["incidentsOverview"]["total"] == 3
    assert data["pagination"]["total"] == 5

    # Try to filter by ambulance 8
    response_ignored = await client.get("/api/v1/dashboard/mobile?ambulanceId=8&limit=10&skip=0", headers=headers)
    assert response_ignored.status_code == 200
    payload_ignored = response_ignored.json()
    assert payload_ignored["data"]["claimsOverview"]["total"] == 1

@pytest.mark.asyncio
async def test_legacy_post_dashboard_mobile(client: AsyncClient, setup_mobile_dashboard_data, admin_token_headers):
    # Call the legacy POST endpoint with superadmin token and body {"id": 1} - used as ambulanceId
    response = await client.post("/api/v1/dashboard/dashboardMobile", json={"id": 1}, headers=admin_token_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    # Check ambulance 1 counts
    assert data["claimsOverview"]["total"] == 2
    assert data["incidentsOverview"]["total"] == 3
