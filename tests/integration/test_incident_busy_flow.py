import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.user import User
from app.models.incident import Incident
from app.models.state import State
from app.models.incident_type import IncidentType
from app.models.ambulance import Ambulance

@pytest_asyncio.fixture
async def setup_busy_flow_records(db: AsyncSession):
    # Ensure state exists
    state_res = await db.execute(select(State).where(State.id == 1))
    state = state_res.scalars().first()
    if not state:
        state = State(id=1, name="FCT")
        db.add(state)
        await db.flush()
        
    # Ensure incident type exists
    inc_type_res = await db.execute(select(IncidentType).where(IncidentType.id == 5))
    inc_type = inc_type_res.scalars().first()
    if not inc_type:
        inc_type = IncidentType(id=5, name="Medical Emergency")
        db.add(inc_type)
        await db.flush()
        
    # Ensure Ambulance exists
    amb_res = await db.execute(select(Ambulance).where(Ambulance.code == "AMB-99"))
    amb = amb_res.scalars().first()
    if not amb:
        amb = Ambulance(
            name="Ambulance 99",
            code="AMB-99",
            state_id=1,
            online=True
        )
        db.add(amb)
        await db.flush()
    
    # Ensure test user exists
    user_res = await db.execute(select(User).where(User.email == "dispatch@test.com"))
    dispatch_user = user_res.scalars().first()
    if not dispatch_user:
        dispatch_user = User(
            email="dispatch@test.com",
            first_name="Dispatch",
            last_name="User",
            user_name="dispatchuser",
            hashed_password="hash",
            is_active=True,
            user_type="SEMSASDISPATCH",
            state_id=1
        )
        db.add(dispatch_user)
        await db.flush()
        
    await db.commit()
    
    return {
        "dispatch_user": dispatch_user,
        "ambulance": amb,
        "incident_type": inc_type,
        "state": state
    }

@pytest.mark.asyncio
async def test_incident_type_last_status(
    client: AsyncClient,
    get_user_token_headers,
    db: AsyncSession,
    setup_busy_flow_records
):
    records = setup_busy_flow_records
    headers = get_user_token_headers(records["dispatch_user"])
    
    # 1. Fetch incident types initially (lastEventStatus should be None)
    response = await client.get("/api/v1/incident-types/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Find type with ID 5
    type_5 = next((t for t in data["data"] if t["id"] == 5), None)
    assert type_5 is not None
    assert type_5["lastEventStatus"] is None
    
    # 2. Get last status directly (should return lastEventStatus as None)
    response = await client.get("/api/v1/incidents/last-event-status?incidentCategoryId=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["lastEventStatus"] is None

    # 3. Create incident with category 5
    inc_payload = {
        "callerName": "John Doe",
        "callerNumber": "08012345678",
        "incidentCategoryId": 5,
        "stateId": 1,
        "eventStatusType": "Reported",
        "patients": []
    }
    response = await client.post("/api/v1/incidents/", json=inc_payload, headers=headers)
    assert response.status_code == 200
    inc_data = response.json()["data"]
    
    # 4. Fetch incident types again, lastEventStatus should now be "Reported"
    response = await client.get("/api/v1/incident-types/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    type_5 = next((t for t in data["data"] if t["id"] == 5), None)
    assert type_5["lastEventStatus"] == "Reported"
    
    # 5. Direct endpoint check
    response = await client.get("/api/v1/incidents/last-event-status?incidentCategoryId=5", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["lastEventStatus"] == "Reported"

@pytest.mark.asyncio
async def test_ambulance_busy_validation_flow(
    client: AsyncClient,
    get_user_token_headers,
    db: AsyncSession,
    setup_busy_flow_records
):
    records = setup_busy_flow_records
    headers = get_user_token_headers(records["dispatch_user"])
    amb_id = records["ambulance"].id
    
    # 1. Create incident 1 assigning ambulance 99
    inc_payload_1 = {
        "callerName": "Caller 1",
        "incidentCategoryId": 5,
        "stateId": 1,
        "ambulanceId": amb_id,
        "eventStatusType": "Reported",
        "patients": []
    }
    response = await client.post("/api/v1/incidents/", json=inc_payload_1, headers=headers)
    assert response.status_code == 200
    inc1_id = response.json()["data"]["id"]
    
    # 2. Check ambulance status - should not be busy yet
    response = await client.get(f"/api/v1/ambulances/{amb_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["eventStatusType"] != "busy"
    
    # 3. Update incident 1 status to "Patient Picked Up"
    update_payload = {
        "eventStatusType": "Patient Picked Up"
    }
    response = await client.patch(f"/api/v1/incidents/{inc1_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    
    # 4. Check ambulance status - should show "busy" now
    response = await client.get(f"/api/v1/ambulances/{amb_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["eventStatusType"] == "busy"
    
    # 5. Attempt to create incident 2 assigning the busy ambulance (should fail)
    inc_payload_2 = {
        "callerName": "Caller 2",
        "incidentCategoryId": 5,
        "stateId": 1,
        "ambulanceId": amb_id,
        "eventStatusType": "Reported",
        "patients": []
    }
    response = await client.post("/api/v1/incidents/", json=inc_payload_2, headers=headers)
    assert response.status_code == 400
    assert "busy" in response.text
    
    # 6. Create incident 2 without ambulance first (success)
    inc_payload_2["ambulanceId"] = None
    response = await client.post("/api/v1/incidents/", json=inc_payload_2, headers=headers)
    assert response.status_code == 200
    inc2_id = response.json()["data"]["id"]
    
    # 7. Attempt to update incident 2 to assign the busy ambulance (should fail)
    update_amb_payload = {
        "ambulanceId": amb_id
    }
    response = await client.patch(f"/api/v1/incidents/{inc2_id}", json=update_amb_payload, headers=headers)
    assert response.status_code == 400
    assert "busy" in response.text
    
    # 8. Update incident 1 to "Patient Dropped Off"
    update_drop_payload = {
        "eventStatusType": "Patient Dropped Off"
    }
    response = await client.patch(f"/api/v1/incidents/{inc1_id}", json=update_drop_payload, headers=headers)
    assert response.status_code == 200, response.text
    
    # 9. Check ambulance status - should no longer be busy
    response = await client.get(f"/api/v1/ambulances/{amb_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["eventStatusType"] != "busy"
    
    # 10. Now assign ambulance to incident 2 (should succeed)
    response = await client.patch(f"/api/v1/incidents/{inc2_id}", json=update_amb_payload, headers=headers)
    assert response.status_code == 200
