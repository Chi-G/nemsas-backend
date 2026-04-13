import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.db.models.user import User, Role, Permission
from src.db.models.ambulance import Ambulance, AmbulanceStatus, Dispatch
from src.db.models.incident import Incident, IncidentStatus, EmergencyType
from src.db.models.run_sheet import RunSheet, RunSheetStatus
from src.core.rbac import RoleName
import uuid
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_etc_workflow(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict, get_user_token_headers
):
    # 1. Setup Incident, Ambulance, and ETC User
    # Create ETC Role
    result = await db.execute(
        select(Role).where(Role.name == RoleName.ETC_STAFF).options(selectinload(Role.permissions))
    )
    etc_role = result.scalars().first()
    if not etc_role:
        etc_role = Role(name=RoleName.ETC_STAFF, description="Hospital Staff", permissions=[])
        db.add(etc_role)
        await db.flush()
    
    # Ensure role has necessary permissions
    from src.core.rbac import Permission as PermissionEnum
    required_perms = [
        PermissionEnum.ETC_READ,
        PermissionEnum.ETC_INTAKE,
        PermissionEnum.ETC_SIGN,
        PermissionEnum.CLAIM_CREATE
    ]
    
    current_perm_names = {p.name for p in etc_role.permissions}
    for perm_name in required_perms:
        if perm_name not in current_perm_names:
            perm_result = await db.execute(select(Permission).where(Permission.name == perm_name))
            perm = perm_result.scalars().first()
            if not perm:
                perm = Permission(name=perm_name, description=f"Permission for {perm_name}")
                db.add(perm)
                await db.flush()
            etc_role.permissions.append(perm)
    
    await db.commit()
    await db.refresh(etc_role, ["permissions"])
        
    # Create ETC Facility User
    etc_user = User(
        email="etc@hospital.com",
        name="Hospital Staff",
        hashed_password="hash",
        is_active=True,
        role_id=etc_role.id,
        provider_id=101 # Our test facility ID
    )
    db.add(etc_user)
    await db.flush()
    etc_headers = get_user_token_headers(etc_user)
    
    # Create Incident
    incident = Incident(
        uuid=str(uuid.uuid4()),
        caller_name="ETCTest",
        caller_phone="08011112222",
        emergency_type=EmergencyType.MEDICAL,
        location_label="Test Patient Address",
        state_id=1,
        status=IncidentStatus.PATIENT_LOADED,
        destination_facility_id=101
    )
    db.add(incident)
    
    amb = Ambulance(
        plate_number="ETC-TEST",
        make_model="Toyota",
        year=2022,
        accreditation_type="BLS",
        state_id=1,
        lga_id=1,
        status=AmbulanceStatus.ACTIVE
    )
    db.add(amb)
    await db.commit()
    
    # Setup a RunSheet (simulating crew already accepted and signed)
    # We need a dispatch first
    dispatch = Dispatch(incident_id=incident.id, ambulance_id=amb.id, crew_id=1)
    db.add(dispatch)
    await db.flush()
    
    run_sheet = RunSheet(
        incident_id=incident.id,
        dispatch_id=dispatch.id,
        patient_name="ETC Test Patient",
        status=RunSheetStatus.CREW_SIGNED, # Ready for ETC
        crew_signature_id=1,
        crew_signed_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(run_sheet)
    await db.commit()
    
    # 2. Test: List Incoming Patients
    response = await client.get("/api/v1/etc/patients/incoming", headers=etc_headers)
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) >= 1
    assert any(p["id"] == incident.id for p in patients)
    
    # 3. Test: Patient Intake
    intake_data = {
        "incident_id": incident.id,
        "arrival_time": datetime.now(timezone.utc).isoformat(),
        "initial_assessment": "Patient stable but requires observation",
        "triage_category": "Yellow",
        "interventions": "Oxygen therapy"
    }
    response = await client.post("/api/v1/etc/intake", json=intake_data, headers=etc_headers)
    assert response.status_code == 200
    assert response.json()["triage_category"] == "Yellow"
    
    # Verify incident status updated to ARRIVED_AT_ETC
    await db.refresh(incident)
    assert incident.status == IncidentStatus.ARRIVED_AT_ETC
    
    # 4. Test: Co-sign Run Sheet
    response = await client.post(f"/api/v1/etc/run-sheets/{run_sheet.id}/cosign", headers=etc_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Fully Co-Signed"
    assert response.json()["etc_signature_id"] == etc_user.id
    
    # 5. Test: Submit Claim
    claim_data = {
        "incident_id": incident.id,
        "amount": 15000.0,
        "notes": "Hospital service fee"
    }
    response = await client.post("/api/v1/etc/claims", json=claim_data, headers=etc_headers)
    assert response.status_code == 200
    assert response.json()["amount"] == 15000.0
    assert response.json()["claim_type"] == "ETC"
