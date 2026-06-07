import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from app.partners.models import PartnerUser, PartnerPledge, PartnerFacility, PartnerAmbulance
from app.models.state import State
from app.models.lga import LGA
from app.models.ward import Ward
from app.models.hospital import Hospital
from app.models.ambulance_type import AmbulanceType

@pytest.mark.asyncio
async def test_partner_auth_lifecycle(client: AsyncClient, db: AsyncSession):
    email = f"partner_test_{uuid.uuid4()}@test.com"
    
    # 1. Register
    reg_payload = {
        "first_name": "Test",
        "last_name": "Partner",
        "email": email,
        "password": "Password@123",
        "phone_number": "123456789",
        "organisation_name": "Test Partner Connect Org"
    }
    
    response = await client.post("/api/v1/partners/auth/register", json=reg_payload)
    assert response.status_code == 200, response.text
    reg_data = response.json()
    assert reg_data["email"] == email
    assert reg_data["first_name"] == "Test"
    
    # 2. Login
    login_payload = {
        "email": email,
        "password": "Password@123"
    }
    response = await client.post("/api/v1/partners/auth/login", json=login_payload)
    assert response.status_code == 200, response.text
    token_data = response.json()
    assert token_data["status"] == "success"
    assert "access_token" in token_data
    
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # 3. Test Dashboard retrieving
    response = await client.get("/api/v1/partners/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    dash_data = response.json()
    assert dash_data["success"] is True
    assert "overViewList" in dash_data["data"]
    assert "overViewCards" in dash_data["data"]

    # 4. Test Ambulances empty/creation flow
    # Retrieve first available location details to build valid models
    state = (await db.execute(select(State).limit(1))).scalar_one_or_none()
    lga = (await db.execute(select(LGA).limit(1))).scalar_one_or_none()
    ward = (await db.execute(select(Ward).limit(1))).scalar_one_or_none()
    hosp = (await db.execute(select(Hospital).limit(1))).scalar_one_or_none()
    amb_type = (await db.execute(select(AmbulanceType).limit(1))).scalar_one_or_none()

    amb_payload = {
        "plate_number": "TEST-1234",
        "make": "Toyota",
        "model": "Hiace",
        "year": 2023,
        "accreditation_type": "BLS",
        "state_id": state.id if state else None,
        "lga_id": lga.id if lga else None,
        "ward_id": ward.id if ward else None,
        "facility_id": hosp.id if hosp else None,
        "vehicle_ownership_type": "private",
        "driver_name": "Test Driver",
        "contact_number": "123456",
        "fuel_type": "CNG",
        "fuel_capacity": "50",
        "communication_devices": ["Radio"],
        "equipments": ["Bandages"]
    }
    
    # Create Ambulance
    response = await client.post("/api/v1/partners/ambulances", json=amb_payload, headers=headers)
    assert response.status_code == 200, response.text
    amb_data = response.json()
    assert amb_data["basicInformation"]["plateNumber"] == "TEST-1234"
    assert amb_data["basicInformation"]["driverName"] == "Test Driver"
    
    # Get Ambulances List
    response = await client.get("/api/v1/partners/ambulances", headers=headers)
    assert response.status_code == 200, response.text
    amb_list = response.json()
    assert amb_list["success"] is True
    assert len(amb_list["data"]["ambulances"]["data"]) == 1
    assert amb_list["data"]["ambulanceSummary"]["total"] == 1
    
    # 5. Facilities empty/creation flow
    fac_payload = {
        "facility_name": "Test Clinic",
        "facility_type": "PHC",
        "facility_location": "urban",
        "ownership_type": "private",
        "communication_devices": ["Radio"],
        "number_of_ambulance": 1,
        "address": "123 Street",
        "contact_information": "080",
        "state_id": state.id if state else None,
        "lga_id": lga.id if lga else None,
        "ward_id": ward.id if ward else None
    }
    response = await client.post("/api/v1/partners/facilities", json=fac_payload, headers=headers)
    assert response.status_code == 200, response.text
    fac_data = response.json()
    assert fac_data["facilityName"] == "Test Clinic"
    assert fac_data["ownershipType"] == "private"
    
    # Get Facilities List
    response = await client.get("/api/v1/partners/facilities", headers=headers)
    assert response.status_code == 200, response.text
    fac_list = response.json()
    assert fac_list["success"] is True
    assert len(fac_list["data"]["data"]) == 1
    
    # 6. Pledges empty/creation flow
    plg_payload = {
        "contact_details": "080123",
        "donor_name": "Test Donor",
        "pledge_type": "donation",
        "number_of_ambulance": 5,
        "ambulance_type_id": amb_type.id if amb_type else None,
        "state_id": state.id if state else None,
        "lga_id": lga.id if lga else None,
        "ward_id": ward.id if ward else None,
        "facility_id": hosp.id if hosp else None
    }
    response = await client.post("/api/v1/partners/pledges", json=plg_payload, headers=headers)
    assert response.status_code == 200, response.text
    plg_data = response.json()
    assert plg_data["donorName"] == "Test Donor"
    assert plg_data["numberOfAmbulance"] == 5
    
    # Get Pledges List
    response = await client.get("/api/v1/partners/pledges", headers=headers)
    assert response.status_code == 200, response.text
    plg_list = response.json()
    assert plg_list["success"] is True
    assert len(plg_list["data"]["list"]["data"]) == 1
