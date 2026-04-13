import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.ambulance import Ambulance, AmbulanceStatus, Dispatch
from src.db.models.incident import Incident, IncidentStatus, EmergencyType
from src.db.models.run_sheet import RunSheet, RunSheetStatus
import uuid

@pytest.mark.asyncio
async def test_run_sheet_lifecycle(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    # 1. Setup Incident and Ambulance
    incident = Incident(
        uuid=str(uuid.uuid4()),
        caller_name="RunSheetTest",
        caller_phone="08011112222",
        emergency_type=EmergencyType.MEDICAL,
        location_label="Test Patient Address",
        state_id=1,
        status=IncidentStatus.CREATED
    )
    db.add(incident)
    await db.flush()
    
    amb = Ambulance(
        plate_number="RUN-SHEET",
        make_model="Toyota",
        year=2022,
        accreditation_type="BLS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE
    )
    db.add(amb)
    await db.commit()
    
    # 2. Dispatch the ambulance
    response = await client.post(
        f"/api/v1/dispatch/assign?incident_id={incident.id}",
        json=[amb.id],
        headers=admin_token_headers
    )
    assert response.status_code == 200
    dispatch_id = response.json()[0]["id"]
    
    # 3. Accept dispatch (should trigger run sheet creation)
    response = await client.post(
        f"/api/v1/dispatch/{dispatch_id}/accept",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    
    # 4. Verify run sheet exists for the incident
    response = await client.get(
        f"/api/v1/run-sheets/by-incident/{incident.id}",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    run_sheet_data = response.json()
    run_sheet_id = run_sheet_data["id"]
    assert run_sheet_data["status"] == "Draft"
    assert run_sheet_data["dispatch_id"] == dispatch_id
    
    # 5. Progressive Save
    save_data = {
        "patient_name": "John Doe",
        "age": 45,
        "gender": "Male",
        "chief_complaint": "Difficulty breathing",
        "blood_pressure": "140/90",
        "pulse_rate": 88,
        "drug_entries": [
            {
                "custom_drug_name": "Salbutamol",
                "dosage": "5mg",
                "is_reimbursable": True
            }
        ]
    }
    response = await client.post(
        f"/api/v1/run-sheets/{run_sheet_id}/save",
        json=save_data,
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["patient_name"] == "John Doe"
    assert len(response.json()["drug_entries"]) == 1
    
    # 6. Crew Signature (Locking)
    response = await client.post(
        f"/api/v1/run-sheets/{run_sheet_id}/sign",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Awaiting ETC Co-Signature"
    assert response.json()["crew_signature_id"] is not None
    
    # 7. Verify locking: Attempt another save should fail
    response = await client.post(
        f"/api/v1/run-sheets/{run_sheet_id}/save",
        json=save_data,
        headers=admin_token_headers
    )
    assert response.status_code == 400
    assert "locked" in response.json()["detail"].lower()
