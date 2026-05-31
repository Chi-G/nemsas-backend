"""
Integration tests for patient medical interventions / drugs injection
from ETC etc_interventions on the incident endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.etc_intervention import EtcIntervention
from app.models.incident import Incident
from app.models.patient import Patient as PatientModel


@pytest.mark.asyncio
async def test_patient_interventions_split_correctly(
    async_client: AsyncClient,
    db: AsyncSession,
    admin_token_headers: dict,
):
    """
    Given an incident with patients and etc_interventions tagged as '- Drug'
    or '- Procedure', the GET /incidents/{id} endpoint should return each
    patient with:
      - medicalInterventions  listing procedures
      - drugs                 listing drug items
    """
    # Create a minimal incident
    incident = Incident(
        caller_name="Test Caller",
        caller_number="08000000000",
        incident_location="Test Location",
        serial_no="TST-INTV-001",
        state_id=1,
    )
    db.add(incident)
    await db.flush()

    # Add a patient to the incident
    patient = PatientModel(
        first_name="Jane",
        last_name="Doe",
        incident_id=incident.id,
    )
    db.add(patient)
    await db.flush()

    # Add etc_interventions: one drug, two procedures
    drug_item = EtcIntervention(
        id=9001,
        incident_id=incident.id,
        medical_intervention="Paracetamol - Drug",
        drug_id=42,
        price=500.0,
        dose=2.0,
        quantity=3,
        diagnosis="Fever",
    )
    proc1 = EtcIntervention(
        id=9002,
        incident_id=incident.id,
        medical_intervention="IV Line Insertion - Procedure",
        price=1500.0,
        quantity=1,
    )
    proc2 = EtcIntervention(
        id=9003,
        incident_id=incident.id,
        medical_intervention="Wound Dressing - Procedure",
        price=800.0,
        quantity=1,
    )
    db.add_all([drug_item, proc1, proc2])
    await db.commit()

    # Fetch the incident via the API
    response = await async_client.get(
        f"/api/v1/incidents/{incident.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()

    patients = data.get("patients", [])
    assert len(patients) == 1, f"Expected 1 patient, got {len(patients)}"
    p = patients[0]

    medical = p.get("medicalInterventions", [])
    drugs = p.get("drugs", [])

    assert len(medical) == 2, f"Expected 2 procedures, got {len(medical)}: {medical}"
    assert len(drugs) == 1, f"Expected 1 drug, got {len(drugs)}: {drugs}"

    # Validate drug structure
    assert drugs[0]["drugId"] == 42
    assert drugs[0]["medicalIntervention"] == "Paracetamol - Drug"

    # Cleanup
    await db.delete(drug_item)
    await db.delete(proc1)
    await db.delete(proc2)
    await db.delete(patient)
    await db.delete(incident)
    await db.commit()


@pytest.mark.asyncio
async def test_patient_with_no_interventions_returns_empty_lists(
    async_client: AsyncClient,
    db: AsyncSession,
    admin_token_headers: dict,
):
    """
    A patient with no etc_interventions should have empty medicalInterventions
    and drugs lists.
    """
    incident = Incident(
        caller_name="Empty Caller",
        incident_location="Empty Location",
        serial_no="TST-INTV-002",
        state_id=1,
    )
    db.add(incident)
    await db.flush()

    patient = PatientModel(
        first_name="John",
        last_name="Smith",
        incident_id=incident.id,
    )
    db.add(patient)
    await db.commit()

    response = await async_client.get(
        f"/api/v1/incidents/{incident.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()

    patients = data.get("patients", [])
    assert len(patients) == 1
    p = patients[0]

    assert p.get("medicalInterventions") == [], f"Expected [], got {p.get('medicalInterventions')}"
    assert p.get("drugs") == [], f"Expected [], got {p.get('drugs')}"

    # Cleanup
    await db.delete(patient)
    await db.delete(incident)
    await db.commit()
