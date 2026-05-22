import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime

from app.models.claim import Claim, ClaimType, ClaimStatus, ClaimAuditLog
from app.models.user import User
from app.models.incident import Incident
from app.models.run_sheet import RunSheet, RunSheetStatus
from app.models.patient import Patient
from app.models.state import State
from app.models.incident_type import IncidentType

@pytest_asyncio.fixture
async def setup_test_users_and_records(db: AsyncSession):
    # Ensure state exists
    state_res = await db.execute(select(State).where(State.id == 1))
    state = state_res.scalars().first()
    if not state:
        state = State(id=1, name="FCT")
        db.add(state)
        
    # Ensure incident type exists
    inc_type_res = await db.execute(select(IncidentType).where(IncidentType.id == 5))
    inc_type = inc_type_res.scalars().first()
    if not inc_type:
        inc_type = IncidentType(id=5, name="Medical Emergency")
        db.add(inc_type)
        
    await db.flush()
    
    # Setup test users with different roles
    nemsas_admin = User(
        email="nemsas_admin@test.com",
        first_name="NEMSAS",
        last_name="Admin",
        user_name="nemsasadmin",
        hashed_password="hash",
        is_active=True,
        user_type="NEMSASADMIN"
    )
    semsas_user = User(
        email="semsas_user@test.com",
        first_name="SEMSAS",
        last_name="User",
        user_name="semsasuser",
        hashed_password="hash",
        is_active=True,
        user_type="SEMSASUSER",
        state_id=1
    )
    
    db.add_all([nemsas_admin, semsas_user])
    await db.flush()
    
    # Create Incident
    incident = Incident(
        caller_name="Caller One",
        caller_number="08012345678",
        state_id=1,
        incident_category_id=5,
        incident_location="Test Location"
    )
    db.add(incident)
    await db.flush()
    
    # Create Patient first
    patient = Patient(
        first_name="Alice",
        last_name="Smith",
        incident_id=incident.id
    )
    db.add(patient)
    await db.flush()
    
    # Create Runsheet linking Patient ID
    runsheet = RunSheet(
        incident_id=incident.id,
        patient_id=patient.id,
        patient_name="Alice Smith",
        date_added=datetime(2026, 5, 22, 12, 0, 0),
        status=RunSheetStatus.DRAFT
    )
    db.add(runsheet)
    await db.flush()
    
    # Create Claim
    claim = Claim(
        incident_id=incident.id,
        patient_name="Alice Smith",
        claim_type=ClaimType.AMBULANCE,
        amount=15000.0,
        status="Pending"
    )
    db.add(claim)
    await db.commit()
    
    return {
        "nemsas_admin": nemsas_admin,
        "semsas_user": semsas_user,
        "incident": incident,
        "runsheet": runsheet,
        "patient": patient,
        "claim": claim
    }

@pytest.mark.asyncio
async def test_runsheet_filtering_and_searching(
    client: AsyncClient,
    get_user_token_headers,
    setup_test_users_and_records
):
    records = setup_test_users_and_records
    headers = get_user_token_headers(records["nemsas_admin"])
    
    # 1. Search by exact patient name
    response = await client.get("/api/v1/run-sheets/?patient_name=Alice", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["totalCount"] >= 1
    assert data["data"]["items"][0]["patientViewModel"]["firstName"] == "Alice"
    
    # 2. Search by month and year
    response = await client.get("/api/v1/run-sheets/?month=5&year=2026", headers=headers)
    assert response.status_code == 200
    assert response.json()["totalCount"] >= 1
    
    # 3. Search by different month (should return 0)
    response = await client.get("/api/v1/run-sheets/?month=12&year=2026", headers=headers)
    assert response.status_code == 200
    assert response.json()["totalCount"] == 0
    
    # 4. Search by incident category
    response = await client.get("/api/v1/run-sheets/?incident_category_id=5", headers=headers)
    assert response.status_code == 200
    assert response.json()["totalCount"] >= 1

@pytest.mark.asyncio
async def test_claims_approval_restrictions_and_endorsement(
    client: AsyncClient,
    get_user_token_headers,
    db: AsyncSession,
    setup_test_users_and_records
):
    records = setup_test_users_and_records
    semsas_headers = get_user_token_headers(records["semsas_user"])
    nemsas_headers = get_user_token_headers(records["nemsas_admin"])
    claim = records["claim"]
    
    # 1. Attempt to approve as SEMSAS user (should fail with 403)
    response = await client.post(f"/api/v1/claims/{claim.id}/approve", headers=semsas_headers)
    assert response.status_code == 403
    assert "cannot directly approve" in response.json()["error"]
    
    # 2. Endorse as SEMSAS user (should succeed)
    response = await client.post(f"/api/v1/claims/{claim.id}/endorse", headers=semsas_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "Endorsed"
    
    # Check Audit Log for Endorse action
    res = await db.execute(select(ClaimAuditLog).where(ClaimAuditLog.claim_id == claim.id))
    logs = res.scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "Endorse"
    assert logs[0].processed_by_id == records["semsas_user"].id
    
    # 3. Approve as NEMSAS Admin (should succeed)
    response = await client.post(f"/api/v1/claims/{claim.id}/approve", headers=nemsas_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "Approved"
    
    # Check Audit Log for Approve action
    res = await db.execute(select(ClaimAuditLog).where(ClaimAuditLog.claim_id == claim.id))
    logs = res.scalars().all()
    assert len(logs) == 2
    assert logs[1].action == "Approve"
    assert logs[1].processed_by_id == records["nemsas_admin"].id
