import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import date
from app.models.state import State
from app.models.monitoring import Monitoring
from app.models.user import User
from app.core.security import get_password_hash

@pytest_asyncio.fixture
async def setup_dashboard_data(db: AsyncSession):
    # Clean up existing monitoring and user records
    await db.execute(delete(Monitoring))
    await db.execute(delete(User).where(User.email != "admin@test.com"))
    await db.commit()

    # Seed states if not exist
    state_1 = await db.get(State, 1)
    if not state_1:
        state_1 = State(id=1, name="Abia", code="")
        db.add(state_1)

    state_8 = await db.get(State, 8)
    if not state_8:
        state_8 = State(id=8, name="Borno", code="")
        db.add(state_8)

    await db.flush()

    # Seed monitoring records for SEED_YEAR = 2026
    # Month = 1 (January), which is less than the current month (May) so it won't be suppressed
    mon1 = Monitoring(
        year=2026,
        month=1,
        no_of_transport=10,
        no_of_mamii_lgas=2,
        by_tricycle_ambulance=1,
        by_nurtw_driver=1,
        bls=1,
        labor_transportation=1,
        obstetric_transportation=1,
        neonatal_transportation=1,
        bemonc=1,
        cemonc=1,
        maternal_mortalities=1,
        neonatal_mortalities=1,
        state_id=1,
        added_by="System",
        is_active=True
    )

    mon2 = Monitoring(
        year=2026,
        month=1,
        no_of_transport=20,
        no_of_mamii_lgas=3,
        by_tricycle_ambulance=2,
        by_nurtw_driver=2,
        bls=2,
        labor_transportation=2,
        obstetric_transportation=2,
        neonatal_transportation=2,
        bemonc=2,
        cemonc=2,
        maternal_mortalities=2,
        neonatal_mortalities=2,
        state_id=8,
        added_by="System",
        is_active=True
    )

    db.add_all([mon1, mon2])

    # Create a SEMSAS user for State 1 (Abia)
    semsas_user = User(
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

    await db.commit()
    await db.refresh(semsas_user)
    return semsas_user

@pytest.mark.asyncio
async def test_superadmin_monthly_dashboard_scoping(client: AsyncClient, setup_dashboard_data, admin_token_headers):
    # 1. Global View (No filter) - Sum of both Abia (10) and Borno (20) -> 30
    response = await client.get("/api/v1/dashboard/monthly?year=2026", headers=admin_token_headers)
    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    
    january_data = next((m for m in data if m["month"] == "January"), None)
    assert january_data is not None
    assert january_data["noOfTransport"] == 30

    # 2. Filtered View for Abia (stateId=1) -> 10
    response_abia = await client.get("/api/v1/dashboard/monthly?year=2026&stateId=1", headers=admin_token_headers)
    assert response_abia.status_code == 200
    payload_abia = response_abia.json()
    january_abia = next((m for m in payload_abia["data"] if m["month"] == "January"), None)
    assert january_abia is not None
    assert january_abia["noOfTransport"] == 10

    # 3. Filtered View for Borno (stateId=8) -> 20
    response_borno = await client.get("/api/v1/dashboard/monthly?year=2026&stateId=8", headers=admin_token_headers)
    assert response_borno.status_code == 200
    payload_borno = response_borno.json()
    january_borno = next((m for m in payload_borno["data"] if m["month"] == "January"), None)
    assert january_borno is not None
    assert january_borno["noOfTransport"] == 20

@pytest.mark.asyncio
async def test_semsas_monthly_dashboard_scoping(client: AsyncClient, setup_dashboard_data, get_user_token_headers):
    semsas_user = setup_dashboard_data
    headers = get_user_token_headers(semsas_user)

    # 1. Access with no stateId param -> Should default to user's assigned state 1 (Abia) -> 10
    response = await client.get("/api/v1/dashboard/monthly?year=2026", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    january_data = next((m for m in payload["data"] if m["month"] == "January"), None)
    assert january_data is not None
    assert january_data["noOfTransport"] == 10

    # 2. Try to pass stateId=8 (Borno) -> Should be ignored and still default to state 1 -> 10
    response_borno = await client.get("/api/v1/dashboard/monthly?year=2026&stateId=8", headers=headers)
    assert response_borno.status_code == 200
    payload_borno = response_borno.json()
    january_borno = next((m for m in payload_borno["data"] if m["month"] == "January"), None)
    assert january_borno is not None
    assert january_borno["noOfTransport"] == 10
