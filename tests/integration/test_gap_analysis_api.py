import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.reference import State, LGA
from src.db.models.ambulance import Ambulance, AmbulanceStatus, AccreditationType
from src.db.models.partner import Pledge, PledgeStatus
from src.db.models.gap_analysis_summary import GapAnalysisSummary
from src.core.rbac import RoleName
from src.db.models.user import User, Role

@pytest.mark.asyncio
async def test_gap_analysis_lifecycle(client: AsyncClient, db: AsyncSession, admin_token_headers: dict):
    # 1. Setup Data - State with 100,000 population (Target = 2)
    state = State(name="Test State", population=100000)
    db.add(state)
    await db.flush()
    
    lga = LGA(name="Test LGA", state_id=state.id, population=60000) # Target = 2 (round up 1.2)
    db.add(lga)
    await db.flush()
    
    # 2. Add Ambulances
    # 1 Active in LGA
    amb1 = Ambulance(
        plate_number="AMB-001",
        make_model="Toyota Hiace",
        year=2022,
        accreditation_type=AccreditationType.BLS,
        status=AmbulanceStatus.ACTIVE,
        state_id=state.id,
        lga_id=lga.id
    )
    # 1 Pending in State (not LGA)
    amb2 = Ambulance(
        plate_number="AMB-002",
        make_model="Mercedes Sprinter",
        year=2023,
        accreditation_type=AccreditationType.ALS,
        status=AmbulanceStatus.PENDING_VERIFICATION,
        state_id=state.id,
        lga_id=lga.id # Put it in same LGA for simplicity
    )
    db.add_all([amb1, amb2])
    await db.commit()
    
    # 3. Trigger Sync
    response = await client.post("/api/v1/gap-analysis/sync", headers=admin_token_headers)
    assert response.status_code == 202
    
    # 4. Verify National Summary
    response = await client.get("/api/v1/gap-analysis/national", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["national_target"] == 2 # 100,000 / 50,000
    assert data["total_active"] == 1
    assert data["total_gap"] == 1
    
    # 5. Verify State Summary
    response = await client.get("/api/v1/gap-analysis/states", headers=admin_token_headers)
    assert response.status_code == 200
    states = response.json()
    test_state = next(s for s in states if s["region_name"] == "Test State")
    assert test_state["target_ambulances"] == 2
    assert test_state["total_active"] == 1
    assert test_state["total_pending_verification"] == 1
    assert test_state["coverage_percentage"] == 50.0
    assert test_state["color_band"] == "partially served" # 50% is partially served (50-75)
    
    # 6. Verify LGA Summary
    response = await client.get(f"/api/v1/gap-analysis/states/{state.id}/lgas", headers=admin_token_headers)
    assert response.status_code == 200
    lgas = response.json()
    test_lga = next(l for l in lgas if l["region_name"] == "Test LGA")
    assert test_lga["target_ambulances"] == 2 # 60,000 / 50,000 = 1.2 -> 2
    assert test_lga["total_active"] == 1
    assert test_lga["coverage_percentage"] == 50.0

@pytest.mark.asyncio
async def test_partner_contributions(client: AsyncClient, db: AsyncSession, get_user_token_headers):
    # Setup Partner
    role = Role(name=RoleName.PARTNER)
    db.add(role)
    await db.flush()
    
    partner_user = User(
        email="partner@test.com",
        name="Partner User",
        hashed_password="hash",
        is_active=True,
        role_id=role.id
    )
    db.add(partner_user)
    await db.flush()
    
    headers = get_user_token_headers(partner_user)
    
    # Add Ambulance owned by this partner
    amb = Ambulance(
        plate_number="PARTNER-001",
        make_model="Ford Transit",
        year=2021,
        accreditation_type=AccreditationType.BLS,
        status=AmbulanceStatus.ACTIVE,
        state_id=1, # Mock IDs
        lga_id=1,
        partner_id=partner_user.id
    )
    db.add(amb)
    await db.commit()
    
    response = await client.get("/api/v1/gap-analysis/my-contributions", headers=headers)
    assert response.status_code == 200
    contributions = response.json()
    assert len(contributions) == 1
    assert contributions[0]["plate_number"] == "PARTNER-001"
