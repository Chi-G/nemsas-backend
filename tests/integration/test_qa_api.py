import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.incident import Incident, IncidentStatus, IncidentStatusHistory, ComplianceRating
from src.db.models.ambulance import Dispatch, Ambulance, AccreditationType
from src.db.models.user import User
import uuid
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_qa_incidents_list_filtering(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Setup: Create a completed incident
    incident = Incident(
        uuid=str(uuid.uuid4()), 
        location_label="QA Test Scene", 
        status=IncidentStatus.COMPLETED,
        emergency_type="Trauma",
        state_id=1
    )
    db.add(incident)
    await db.flush()
    
    # Add Dispatch for response time
    dispatch = Dispatch(
        incident_id=incident.id,
        ambulance_id=1, # Assume exists from conftest or setup
        crew_id=1,
        dispatch_timestamp=datetime.now() - timedelta(minutes=30)
    )
    db.add(dispatch)
    
    # Add Arrival Status History
    history = IncidentStatusHistory(
        incident_id=incident.id,
        status=IncidentStatus.AT_SCENE,
        changed_at=datetime.now() - timedelta(minutes=10),
        changed_by_id=1
    )
    db.add(history)
    await db.commit()

    response = await client.get("/api/v1/qa/incidents", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    item = data[0]
    assert item["response_time_minutes"] is not None
    assert abs(item["response_time_minutes"] - 20) < 1 # Should be roughly 20 mins

@pytest.mark.asyncio
async def test_create_qa_finding_validation(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # Setup
    incident = Incident(uuid=str(uuid.uuid4()), location_label="Validation Test", status=IncidentStatus.COMPLETED, emergency_type="Medical")
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    # 1. Non-Compliant without findings text -> Should fail
    response = await client.post(
        "/api/v1/qa/",
        json={
            "incident_id": incident.id,
            "compliance_rating": "Non-Compliant",
            "findings_text": "  " # Empty or whitespace
        },
        headers=admin_token_headers
    )
    assert response.status_code == 400
    assert "mandatory" in response.json()["detail"].lower()

    # 2. Compliant -> Should succeed
    response = await client.post(
        "/api/v1/qa/",
        json={
            "incident_id": incident.id,
            "compliance_rating": "Compliant",
            "findings_text": "Everything looked good."
        },
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["compliance_rating"] == "Compliant"
