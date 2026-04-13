import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.incident import Incident, EmergencyType, IncidentChannel
from src.db.models.user import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_ussd_flow_full(client: AsyncClient, db: AsyncSession):
    # 1. Start session
    payload = {
        "sessionId": "test_ussd_123",
        "serviceCode": "*123#",
        "phoneNumber": "+2348011112222",
        "text": ""
    }
    response = await client.post("/api/v1/ussd-sms/ussd", data=payload)
    assert response.status_code == 200
    assert "CON" in response.text
    assert "Medical" in response.text

    # 2. Select Medical
    payload["text"] = "1"
    response = await client.post("/api/v1/ussd-sms/ussd", data=payload)
    assert response.status_code == 200
    assert "CON" in response.text
    assert "location" in response.text.lower()

    # 3. Enter Location -> Confirmation Menu
    payload["text"] = "1*Abuja Central"
    response = await client.post("/api/v1/ussd-sms/ussd", data=payload)
    assert response.status_code == 200
    assert "CON" in response.text
    assert "confirm" in response.text.lower()

    # 4. Confirm -> Finalizes
    payload["text"] = "1*Abuja Central*1"
    response = await client.post("/api/v1/ussd-sms/ussd", data=payload)
    assert response.status_code == 200
    assert "END" in response.text
    assert "reported" in response.text.lower()

    # 5. Verify DB
    query = await db.execute(select(Incident).where(Incident.caller_phone == "+2348011112222"))
    incident = query.scalars().first()
    assert incident is not None
    assert incident.location_label == "Abuja Central"
    assert incident.emergency_type == EmergencyType.MEDICAL
    assert incident.channel == IncidentChannel.USSD

@pytest.mark.asyncio
async def test_sms_valid_format(client: AsyncClient, db: AsyncSession):
    payload = {
        "from": "+2348022223333",
        "to": "12345",
        "text": "EMERGENCY TRAUMA at Berger Bus Stop",
        "date": "2024-04-13",
        "id": "sms_id_1"
    }
    response = await client.post("/api/v1/ussd-sms/sms", data=payload)
    assert response.status_code == 200
    assert "reported" in response.json()["message"].lower()

    # Verify DB
    query = await db.execute(select(Incident).where(Incident.caller_phone == "+2348022223333"))
    incident = query.scalars().first()
    assert incident is not None
    assert incident.location_label == "Berger Bus Stop"
    assert incident.emergency_type == EmergencyType.TRAUMA
    assert incident.channel == IncidentChannel.SMS

@pytest.mark.asyncio
async def test_sms_invalid_format(client: AsyncClient):
    payload = {
        "from": "+2348022223334",
        "to": "12345",
        "text": "help me",
        "date": "2024-04-13",
        "id": "sms_id_2"
    }
    response = await client.post("/api/v1/ussd-sms/sms", data=payload)
    assert response.status_code == 200
    assert "invalid format" in response.json()["message"].lower()

@pytest.mark.asyncio
async def test_voice_callback(client: AsyncClient, db: AsyncSession):
    payload = {
        "isActive": "1",
        "sessionId": "voice_test_789",
        "direction": "Inbound",
        "callerNumber": "+2348033334444",
        "destinationNumber": "+234701234567"
    }
    response = await client.post("/api/v1/ussd-sms/voice", data=payload)
    assert response.status_code == 200
    assert '<?xml version="1.0" encoding="UTF-8"?>' in response.text
    assert "<Say" in response.text

    # Verify DB
    query = await db.execute(select(Incident).where(Incident.caller_phone == "+2348033334444"))
    incident = query.scalars().first()
    assert incident is not None
    assert incident.channel == IncidentChannel.CALL
    assert incident.location_confirmed is False
