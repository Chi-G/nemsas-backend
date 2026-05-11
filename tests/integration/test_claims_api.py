import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.incident import Incident, EmergencyType
from src.db.models.claim import Claim, ClaimType, ClaimStatus, ClaimAuditLog
from src.db.models.user import User, Role
from src.core.rbac import RoleName
import uuid
from datetime import datetime

import pytest_asyncio
from sqlalchemy import select

@pytest_asyncio.fixture
async def sample_data(db: AsyncSession):
    # Setup Role
    role_res = await db.execute(select(Role).where(Role.name == RoleName.CLAIMS_STAFF))
    role = role_res.scalars().first()
    if not role:
        role = Role(name=RoleName.CLAIMS_STAFF, description="Claims Staff")
        db.add(role)
        await db.flush()
    
    # Setup User
    user = User(
        email="claims@test.com",
        name="Claims User",
        hashed_password="hash",
        is_active=True,
        role_id=role.id
    )
    db.add(user)
    
    # Setup Incident
    incident = Incident(
        uuid=str(uuid.uuid4()),
        location_label="Test Location",
        emergency_type=EmergencyType.MEDICAL,
        state_id=1,
        lga_id=1
    )
    db.add(incident)
    await db.flush()
    
    # Setup Claims
    amb_claim = Claim(
        incident_id=incident.id,
        user_id=user.id,
        claim_type=ClaimType.AMBULANCE,
        amount=15000.0,
        status=ClaimStatus.PENDING
    )
    etc_claim = Claim(
        incident_id=incident.id,
        user_id=user.id,
        claim_type=ClaimType.ETC,
        amount=5000.0,
        status=ClaimStatus.PENDING
    )
    db.add_all([amb_claim, etc_claim])
    await db.commit()
    
    return {"user": user, "incident": incident, "amb_claim": amb_claim, "etc_claim": etc_claim}

@pytest.mark.asyncio
async def test_list_claims_paired(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Setup some data manually if fixture is not used here
    incident = Incident(uuid=str(uuid.uuid4()), location_label="API Test", emergency_type=EmergencyType.TRAUMA, state_id=1)
    db.add(incident)
    await db.flush()
    c1 = Claim(incident_id=incident.id, user_id=1, claim_type=ClaimType.AMBULANCE, amount=15000, status=ClaimStatus.PENDING)
    c2 = Claim(incident_id=incident.id, user_id=1, claim_type=ClaimType.ETC, amount=5000, status=ClaimStatus.PENDING)
    db.add_all([c1, c2])
    await db.commit()

    response = await client.get("/api/v1/claims/", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    pair = data[0]
    assert pair["incident_id"] == incident.id
    assert pair["ambulance_claim"]["amount"] == 15000
    assert pair["etc_claim"]["amount"] == 5000

@pytest.mark.asyncio
async def test_process_claim_approve(client: AsyncClient, admin_token_headers, db: AsyncSession):
    c1 = Claim(incident_id=1, user_id=1, claim_type=ClaimType.AMBULANCE, amount=15000, status=ClaimStatus.PENDING)
    db.add(c1)
    await db.commit()
    await db.refresh(c1)

    response = await client.patch(
        f"/api/v1/claims/{c1.id}/process", 
        json={"status": "Approved"}, 
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Approved"
    
    # Check Audit Log
    stmt = select(ClaimAuditLog).where(ClaimAuditLog.claim_id == c1.id)
    res = await db.execute(stmt)
    audit = res.scalars().first()
    assert audit is not None
    assert audit.action == "Approve"

@pytest.mark.asyncio
async def test_process_claim_reject_needs_reason(client: AsyncClient, admin_token_headers, db: AsyncSession):
    c = Claim(incident_id=1, user_id=1, claim_type=ClaimType.ETC, amount=5000, status=ClaimStatus.PENDING)
    db.add(c)
    await db.commit()
    await db.refresh(c)

    # Missing reason
    response = await client.patch(
        f"/api/v1/claims/{c.id}/process", 
        json={"status": "Rejected"}, 
        headers=admin_token_headers
    )
    assert response.status_code == 400
    assert "reason" in response.json()["detail"].lower()

    # With reason
    response = await client.patch(
        f"/api/v1/claims/{c.id}/process", 
        json={"status": "Rejected", "rejection_reason": "Invalid documents"}, 
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Rejected"

@pytest.mark.asyncio
async def test_export_claims_csv(client: AsyncClient, admin_token_headers):
    response = await client.get("/api/v1/claims/export", headers=admin_token_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Incident UUID" in response.text
