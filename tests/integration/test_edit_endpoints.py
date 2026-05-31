import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User
from app.models.state import State
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.core.security import get_password_hash

@pytest_asyncio.fixture
async def setup_edit_records(db: AsyncSession):
    # Clean up existing records to prevent unique/duplicate ID constraint failures
    await db.execute(delete(User).where(User.email != "admin@test.com"))
    await db.execute(delete(Ambulance))
    await db.execute(delete(Hospital))
    await db.commit()

    # Setup States
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

    # Create Users
    superadmin = User(
        email="superadmin@example.com",
        first_name="Super",
        last_name="Admin",
        user_name="superadmin_edit",
        hashed_password=get_password_hash("password123"),
        user_type="SUPERADMINISTRATOR",
        is_active=True
    )
    db.add(superadmin)

    state1_admin = User(
        email="admin1_edit@example.com",
        first_name="State1",
        last_name="Admin",
        user_name="state1_admin_edit",
        hashed_password=get_password_hash("password123"),
        user_type="ADMINSEMSASUSER",
        state_id=1,
        is_active=True
    )
    db.add(state1_admin)

    user_state1 = User(
        email="user1_edit@example.com",
        first_name="User",
        last_name="One",
        user_name="user_state1_edit",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASUSER",
        state_id=1,
        is_active=True
    )
    db.add(user_state1)

    user_state2 = User(
        email="user2_edit@example.com",
        first_name="User",
        last_name="Two",
        user_name="user_state2_edit",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASUSER",
        state_id=2,
        is_active=True
    )
    db.add(user_state2)

    dispatch_user = User(
        email="dispatch_edit@example.com",
        first_name="Dispatch",
        last_name="User",
        user_name="dispatch_user_edit",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASDISPATCH",
        state_id=1,
        is_active=True
    )
    db.add(dispatch_user)

    # Create Ambulances
    amb_state1 = Ambulance(
        id=10,
        name="Ambulance State 1",
        code="AMB-ST1",
        state_id=1,
        online=True
    )
    db.add(amb_state1)

    amb_state2 = Ambulance(
        id=11,
        name="Ambulance State 2",
        code="AMB-ST2",
        state_id=2,
        online=True
    )
    db.add(amb_state2)

    # Create Hospitals
    hosp_state1 = Hospital(
        id=20,
        name="Hospital State 1",
        state_id=1,
        location="Location 1"
    )
    db.add(hosp_state1)

    hosp_state2 = Hospital(
        id=21,
        name="Hospital State 2",
        state_id=2,
        location="Location 2"
    )
    db.add(hosp_state2)

    await db.commit()

    return {
        "superadmin": superadmin,
        "state1_admin": state1_admin,
        "user_state1": user_state1,
        "user_state2": user_state2,
        "dispatch_user": dispatch_user,
        "amb_state1": amb_state1,
        "amb_state2": amb_state2,
        "hosp_state1": hosp_state1,
        "hosp_state2": hosp_state2
    }


# ==================== User Edit Tests ====================

@pytest.mark.asyncio
async def test_superadmin_can_edit_any_user(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    superadmin = setup_edit_records["superadmin"]
    target_user = setup_edit_records["user_state2"]
    
    headers = get_user_token_headers(superadmin)
    
    payload = {
        "firstName": "UpdatedName",
        "email": "newemail@example.com",
        "ambulanceId": 11,
        "emergencyTreatmentCenterId": 21,
        "password": "newpassword123"
    }
    
    response = await client.patch(f"/api/v1/users/{target_user.id}", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["firstName"] == "UpdatedName"
    assert data["data"]["email"] == "newemail@example.com"
    assert data["data"]["ambulanceId"] == 11
    assert data["data"]["emergencyTreatmentCenterId"] == 21
    
    # Verify in database
    await db.close()
    db_user_res = await db.execute(select(User).where(User.id == target_user.id))
    db_user = db_user_res.scalars().first()
    assert db_user is not None
    assert db_user.first_name == "UpdatedName"
    assert db_user.email == "newemail@example.com"
    assert db_user.ambulance_id == 11
    assert db_user.emergency_treatment_center_id == 21
    assert db_user.etc_id == 21
    assert db_user.hashed_password.startswith("$2b$12$")


@pytest.mark.asyncio
async def test_state_admin_can_edit_user_in_same_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_user = setup_edit_records["user_state1"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "lastName": "UpdatedLastName"
    }
    
    response = await client.patch(f"/api/v1/users/{target_user.id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["lastName"] == "UpdatedLastName"


@pytest.mark.asyncio
async def test_state_admin_cannot_edit_user_in_different_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_user = setup_edit_records["user_state2"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "firstName": "HackName"
    }
    
    response = await client.patch(f"/api/v1/users/{target_user.id}", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_state_admin_cannot_assign_user_to_different_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_user = setup_edit_records["user_state1"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "stateId": 2  # State admin 1 tries to change user's state to State 2
    }
    
    response = await client.patch(f"/api/v1/users/{target_user.id}", json=payload, headers=headers)
    assert response.status_code == 403


# ==================== Ambulance Edit Tests ====================

@pytest.mark.asyncio
async def test_superadmin_can_edit_any_ambulance(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    superadmin = setup_edit_records["superadmin"]
    target_amb = setup_edit_records["amb_state2"]
    
    headers = get_user_token_headers(superadmin)
    
    payload = {
        "driverName": "Ambulance Driver",
        "contactNumber": "08011223344",
        "online": False
    }
    
    response = await client.patch(f"/api/v1/ambulances/{target_amb.id}", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["driverName"] == "Ambulance Driver"
    assert data["data"]["contactNumber"] == "08011223344"
    assert data["data"]["online"] is False


@pytest.mark.asyncio
async def test_state_admin_can_edit_ambulance_in_same_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_amb = setup_edit_records["amb_state1"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "location": "New Parade Ground"
    }
    
    response = await client.patch(f"/api/v1/ambulances/{target_amb.id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["location"] == "New Parade Ground"


@pytest.mark.asyncio
async def test_state_admin_cannot_edit_ambulance_in_different_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_amb = setup_edit_records["amb_state2"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "location": "Hack Location"
    }
    
    response = await client.patch(f"/api/v1/ambulances/{target_amb.id}", json=payload, headers=headers)
    assert response.status_code == 403


# ==================== Hospital Edit Tests ====================

@pytest.mark.asyncio
async def test_superadmin_can_edit_any_hospital(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    superadmin = setup_edit_records["superadmin"]
    target_hosp = setup_edit_records["hosp_state2"]
    
    headers = get_user_token_headers(superadmin)
    
    payload = {
        "location": "Updated Location",
        "nhiAorSHIA": "NHIA"
    }
    
    response = await client.patch(f"/api/v1/hospitals/{target_hosp.id}", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["location"] == "Updated Location"
    assert data["data"]["nhiAorSHIA"] == "NHIA"


@pytest.mark.asyncio
async def test_state_admin_can_edit_hospital_in_same_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_hosp = setup_edit_records["hosp_state1"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "name": "New Hospital Name"
    }
    
    response = await client.patch(f"/api/v1/hospitals/{target_hosp.id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Hospital Name"


@pytest.mark.asyncio
async def test_state_admin_cannot_edit_hospital_in_different_state(
    client: AsyncClient, db: AsyncSession, setup_edit_records, get_user_token_headers
):
    state1_admin = setup_edit_records["state1_admin"]
    target_hosp = setup_edit_records["hosp_state2"]
    
    headers = get_user_token_headers(state1_admin)
    
    payload = {
        "name": "Hack Hospital Name"
    }
    
    response = await client.patch(f"/api/v1/hospitals/{target_hosp.id}", json=payload, headers=headers)
    assert response.status_code == 403
