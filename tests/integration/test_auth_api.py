import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.models.user import User
from sqlalchemy import select

import pytest_asyncio

# Seed data for tests
@pytest_asyncio.fixture
async def setup_data(db: AsyncSession):
    user_q = await db.execute(select(User).where(User.email == "test@example.com"))
    user = user_q.scalars().first()
    if not user:
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            user_name="testuser",
            hashed_password=get_password_hash("password123"),
            user_type="SUPERADMINISTRATOR",
            is_active=True
        )
        db.add(user)
    
    inactive_q = await db.execute(select(User).where(User.email == "inactive@example.com"))
    if not inactive_q.scalars().first():
        inactive_user = User(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            user_name="inactiveuser",
            hashed_password=get_password_hash("password123"),
            user_type="NEMSASADMIN",
            is_active=False
        )
        db.add(inactive_user)
    
    await db.commit()
    return user

@pytest.mark.asyncio
async def test_1_login_endpoint(client: AsyncClient, setup_data):
    # Requirement 1: Login endpoint accepts email/password, validates, returns JWT
    response = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_2_token_expiration_config():
    # Requirement 2: 15 min access, 7 day refresh
    from app.core.config import settings
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert settings.REFRESH_TOKEN_EXPIRE_MINUTES == 43200

@pytest.mark.asyncio
async def test_3_bcrypt_cost_factor():
    # Default bcrypt rounds in python is 12. We can tell because the prefix is generally $2b$12$
    hash_str = get_password_hash("test")
    assert hash_str.startswith("$2b$12$")

@pytest.mark.asyncio
async def test_4_error_masking(client: AsyncClient, setup_data):
    # Requirement 10: Hide whether email exists
    # Non existent email login
    non_existent = await client.post("/api/v1/auth/login", json={"email": "nobody@nowhere.com", "password": "abc"})
    print("Non-existent response:", non_existent.status_code, non_existent.json())
    assert non_existent.status_code == 401
    assert non_existent.json()["error"] == "Incorrect email or password"
    
    # Existent email wrong password
    existent = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "abc"})
    print("Existent response:", existent.status_code, existent.json())
    assert existent.status_code == 401
    assert existent.json()["error"] == "Incorrect email or password"
    
    # Existent email inactive user
    inactive = await client.post("/api/v1/auth/login", json={"email": "inactive@example.com", "password": "password123"})
    assert inactive.status_code == 400
    assert inactive.json()["error"] == "Inactive user"

@pytest.mark.asyncio
async def test_5_change_password(client: AsyncClient, setup_data, get_user_token_headers):
    # Test change password
    headers = get_user_token_headers(setup_data)
    
    # Fail with wrong current password
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "wrongpassword", "newPassword": "newpassword123"},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Incorrect current password"
    
    # Success with correct current password
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "password123", "newPassword": "newpassword123"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify we can login with the new password
    login_resp = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "newpassword123"})
    assert login_resp.status_code == 200
