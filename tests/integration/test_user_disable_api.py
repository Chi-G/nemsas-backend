import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.state import State
from app.core.security import get_password_hash

@pytest_asyncio.fixture
async def setup_user_records(db: AsyncSession):
    # Setup two states: State 1 and State 2
    state1_res = await db.execute(select(State).where(State.id == 1))
    state1 = state1_res.scalars().first()
    if not state1:
        state1 = State(id=1, name="State A")
        db.add(state1)
        
    state2_res = await db.execute(select(State).where(State.id == 2))
    state2 = state2_res.scalars().first()
    if not state2:
        state2 = State(id=2, name="State B")
        db.add(state2)
        
    await db.flush()

    # Create Superadmin User
    superadmin = User(
        email="superadmin@example.com",
        first_name="Super",
        last_name="Admin",
        user_name="superadmin_test",
        hashed_password=get_password_hash("password123"),
        user_type="SUPERADMINISTRATOR",
        is_active=True
    )
    db.add(superadmin)

    # Create State Admin for State 1
    state1_admin = User(
        email="admin1@example.com",
        first_name="State1",
        last_name="Admin",
        user_name="state1_admin",
        hashed_password=get_password_hash("password123"),
        user_type="ADMINSEMSASUSER",
        state_id=1,
        is_active=True
    )
    db.add(state1_admin)

    # Create Regular User in State 1
    user_state1 = User(
        email="user1@example.com",
        first_name="User",
        last_name="One",
        user_name="user_state1",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASUSER",
        state_id=1,
        is_active=True
    )
    db.add(user_state1)

    # Create Regular User in State 2
    user_state2 = User(
        email="user2@example.com",
        first_name="User",
        last_name="Two",
        user_name="user_state2",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASUSER",
        state_id=2,
        is_active=True
    )
    db.add(user_state2)

    # Create Non-admin User
    dispatch_user = User(
        email="dispatch@example.com",
        first_name="Dispatch",
        last_name="User",
        user_name="dispatch_user",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASDISPATCH",
        state_id=1,
        is_active=True
    )
    db.add(dispatch_user)

    await db.commit()

    return {
        "superadmin": superadmin,
        "state1_admin": state1_admin,
        "user_state1": user_state1,
        "user_state2": user_state2,
        "dispatch_user": dispatch_user
    }


@pytest.mark.asyncio
async def test_superadmin_can_disable_any_user(
    client: AsyncClient, db: AsyncSession, setup_user_records, get_user_token_headers
):
    superadmin = setup_user_records["superadmin"]
    target_user = setup_user_records["user_state2"]
    
    headers = get_user_token_headers(superadmin)
    
    # Disable user
    response = await client.delete(f"/api/v1/users/{target_user.id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "User successfully disabled"
    assert data["data"]["id"] == str(target_user.id)
    assert data["data"]["isActive"] is False
    
    # Verify in DB that the record exists and is disabled (not deleted)
    await db.close()  # Refresh session
    db_user_res = await db.execute(select(User).where(User.id == target_user.id))
    db_user = db_user_res.scalars().first()
    assert db_user is not None
    assert db_user.is_active is False


@pytest.mark.asyncio
async def test_state_admin_can_disable_user_in_same_state(
    client: AsyncClient, db: AsyncSession, setup_user_records, get_user_token_headers
):
    state1_admin = setup_user_records["state1_admin"]
    target_user = setup_user_records["user_state1"]
    
    headers = get_user_token_headers(state1_admin)
    
    # Disable user in the same state
    response = await client.delete(f"/api/v1/users/{target_user.id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "User successfully disabled"
    assert data["data"]["isActive"] is False
    
    # Verify in DB
    db_user_res = await db.execute(select(User).where(User.id == target_user.id))
    db_user = db_user_res.scalars().first()
    assert db_user is not None
    assert db_user.is_active is False


@pytest.mark.asyncio
async def test_state_admin_cannot_disable_user_in_different_state(
    client: AsyncClient, db: AsyncSession, setup_user_records, get_user_token_headers
):
    state1_admin = setup_user_records["state1_admin"]
    target_user = setup_user_records["user_state2"]
    
    headers = get_user_token_headers(state1_admin)
    
    # Attempt to disable user in different state
    response = await client.delete(f"/api/v1/users/{target_user.id}", headers=headers)
    assert response.status_code == 403
    
    # Verify user is still active in DB
    db_user_res = await db.execute(select(User).where(User.id == target_user.id))
    db_user = db_user_res.scalars().first()
    assert db_user is not None
    assert db_user.is_active is True


@pytest.mark.asyncio
async def test_non_admin_role_cannot_disable_users(
    client: AsyncClient, db: AsyncSession, setup_user_records, get_user_token_headers
):
    dispatch_user = setup_user_records["dispatch_user"]
    target_user = setup_user_records["user_state1"]
    
    headers = get_user_token_headers(dispatch_user)
    
    # Attempt to disable
    response = await client.delete(f"/api/v1/users/{target_user.id}", headers=headers)
    assert response.status_code == 403
    
    # Verify user is still active in DB
    db_user_res = await db.execute(select(User).where(User.id == target_user.id))
    db_user = db_user_res.scalars().first()
    assert db_user is not None
    assert db_user.is_active is True


@pytest.mark.asyncio
async def test_disable_non_existent_user_returns_404(
    client: AsyncClient, setup_user_records, get_user_token_headers
):
    superadmin = setup_user_records["superadmin"]
    headers = get_user_token_headers(superadmin)
    
    random_uuid = uuid.uuid4()
    response = await client.delete(f"/api/v1/users/{random_uuid}", headers=headers)
    assert response.status_code == 404
