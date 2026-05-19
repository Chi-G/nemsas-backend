import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.incident import Incident
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.hospital_type import HospitalType
from app.models.ambulance import Ambulance
from app.models.run_sheet import RunSheet
from app.models.transfer_form import TransferForm

@pytest.mark.asyncio
async def test_patient_transfer_forms_lifecycle(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    # 1. Seed dependencies: Medic User, Hospice User, Patient, Incident, ETC, Ambulance, RunSheet
    medic = User(
        email="medic@test.com",
        first_name="Medic",
        last_name="User",
        user_name="medic",
        hashed_password="hash",
        is_active=True,
        user_type="MEDIC"
    )
    hospice = User(
        email="hospice@test.com",
        first_name="Hospice",
        last_name="User",
        user_name="hospice",
        hashed_password="hash",
        is_active=True,
        user_type="HOSPICE"
    )
    db.add(medic)
    db.add(hospice)
    await db.flush()

    patient = Patient(
        first_name="John",
        last_name="Doe",
        sex=1,
        phone_number="08011112222"
    )
    db.add(patient)
    await db.flush()

    incident = Incident(
        caller_name="TransferTest",
        caller_number="08011112222",
        incident_location="Test Address",
        incident_status_type="Reported"
    )
    db.add(incident)
    await db.flush()

    etc_type = HospitalType(
        name="ETC",
        description="Emergency Treatment Center"
    )
    db.add(etc_type)
    await db.flush()

    etc = Hospital(
        name="Emergency Treatment Center Test",
        hospital_type=etc_type,
        state_id=1,
        lga_id=1,
        address1="123 Test St"
    )
    db.add(etc)
    await db.flush()

    ambulance = Ambulance(
        name="TF-AMB",
        code="TF-AMB",
        plate_number="TF-AMB",
        make="Toyota",
        model="Hiace",
        year="2021"
    )
    db.add(ambulance)
    await db.flush()

    run_sheet = RunSheet(
        incident_id=incident.id,
        ambulance_id=ambulance.id,
        status="Draft"
    )
    db.add(run_sheet)
    await db.commit()

    # 2. Test POST /api/v1/TransferForms/add
    add_payload = {
        "incident_id": incident.id,
        "medic_user_id": str(medic.id),
        "hospice_user_id": str(hospice.id),
        "patient_id": patient.id,
        "etc_id": etc.id,
        "run_sheet_id": run_sheet.id
    }
    response = await client.post(
        "/api/v1/TransferForms/add",
        json=add_payload,
        headers=admin_token_headers
    )
    assert response.status_code == 200, response.text
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["message"] == "Transfer Form successfully created"
    transfer_form_id = res_data["data"]["id"]
    assert res_data["data"]["approve"] is False  # default value

    # 3. Test GET /api/v1/TransferForms/get (all & filtered)
    response = await client.get(
        "/api/v1/TransferForms/get",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert len(res_data["data"]["items"]) >= 1

    # Filtered by incident_id
    response = await client.get(
        f"/api/v1/TransferForms/get?incident_id={incident.id}",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 1

    # 4. Test POST /api/v1/TransferForms/getSingle
    response = await client.post(
        "/api/v1/TransferForms/getSingle",
        json={"id": transfer_form_id},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["id"] == transfer_form_id

    # 5. Test POST /api/v1/TransferForms/getByAssignedAmbulance
    response = await client.post(
        "/api/v1/TransferForms/getByAssignedAmbulance",
        json={"id": ambulance.id},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert len(res_data["data"]["items"]) == 1
    assert res_data["data"]["items"][0]["id"] == transfer_form_id

    # 6. Test POST /api/v1/TransferForms/getByAssignedETC
    response = await client.post(
        "/api/v1/TransferForms/getByAssignedETC",
        json={"id": etc.id},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert len(res_data["data"]["items"]) == 1
    assert res_data["data"]["items"][0]["id"] == transfer_form_id

    # 7. Test PUT /api/v1/TransferForms/update
    update_payload = {
        "approve": True
    }
    response = await client.put(
        f"/api/v1/TransferForms/update?id={transfer_form_id}",
        json=update_payload,
        headers=admin_token_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["approve"] is True

    # 8. Test DELETE /api/v1/TransferForms/delete
    response = await client.request(
        "DELETE",
        "/api/v1/TransferForms/delete",
        json={"id": transfer_form_id},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["message"] == "Transfer Form successfully deleted"

    # Verify deleted
    response = await client.post(
        "/api/v1/TransferForms/getSingle",
        json={"id": transfer_form_id},
        headers=admin_token_headers
    )
    assert response.status_code == 404
