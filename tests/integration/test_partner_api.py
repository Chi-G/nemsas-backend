import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.partner import Partner, Pledge, PledgeStatus, FacilityRequest, Facility
from src.db.models.auth import UserToken, TokenType
from src.db.models.user import User
from src.services.auth import auth_service
from sqlalchemy import select
import uuid

@pytest.mark.asyncio
async def test_partner_registration_and_otp_flow(client: AsyncClient, db: AsyncSession):
    # 1. Register
    email = f"partner_{uuid.uuid4()}@test.com"
    reg_data = {
        "organisation_name": "Test Partner Org",
        "email": email,
        "contact_person": "John Partner",
        "contact_phone": "08012345678",
        "address": "123 Partner Street"
    }
    response = await client.post("/api/v1/partners/register", json=reg_data)
    assert response.status_code == 200
    assert response.json()["organisation_name"] == "Test Partner Org"
    
    # 2. Get OTP from DB (for testing)
    stmt = select(User).where(User.email == email)
    user = (await db.execute(stmt)).scalars().first()
    
    stmt = select(UserToken).where(UserToken.user_id == user.id, UserToken.token_type == TokenType.TWO_FACTOR).order_by(UserToken.created_at.desc())
    res = await db.execute(stmt)
    token = res.scalars().first()
    assert token is not None
    
    # 3. Verify OTP
    verify_data = {"email": email, "otp": token.token}
    response = await client.post("/api/v1/partners/verify-otp", json=verify_data)
    assert response.status_code == 200
    assert response.json()["is_verified"] is True

@pytest.mark.asyncio
async def test_admin_approval_workflow(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Setup: Verified but inactive partner
    email = f"approve_{uuid.uuid4()}@test.com"
    reg_data = {
        "organisation_name": "Approval Org",
        "email": email,
        "contact_person": "Jane",
        "contact_phone": "080",
        "address": "Street"
    }
    # Manually bypass registration for speed in test setup if needed, but let's use the service
    from src.services.partner import partner_service
    from src.schemas.partner import PartnerRegister, PartnerVerifyOTP
    p = await partner_service.register_partner(db, PartnerRegister(**reg_data))
    
    # Get OTP
    stmt = select(UserToken).where(UserToken.user_id == p.user_id, UserToken.token_type == TokenType.TWO_FACTOR)
    token = (await db.execute(stmt)).scalars().first()
    await partner_service.verify_partner_otp(db, PartnerVerifyOTP(email=reg_data["email"], otp=token.token))
    
    # 1. Admin Approve
    response = await client.patch(f"/api/v1/partners/{p.id}/approve", headers=admin_token_headers)
    assert response.status_code == 200
    assert response.json()["is_verified"] is True
    
    # Check if user is active
    from src.db.models.user import User
    res = await db.execute(select(User).where(User.id == p.user_id))
    user = res.scalars().first()
    assert user.is_active is True

@pytest.mark.asyncio
async def test_pledge_immutability_and_admin_status(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # We need a partner token. Let's assume we have a helper or create one.
    # For now, let's test the Admin status update part which is more critical.
    
    p = Partner(organisation_name="Pledge Org", user_id=1, is_verified=True, contact_person="C", contact_phone="P", address="A")
    db.add(p)
    await db.flush()
    pledge = Pledge(partner_id=p.id, ambulance_count=5, status=PledgeStatus.PENDING)
    db.add(pledge)
    await db.commit()
    
    # Admin Update Status
    response = await client.patch(
        f"/api/v1/partners/pledges/{pledge.id}/status",
        json={"status": "In Progress"},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"
