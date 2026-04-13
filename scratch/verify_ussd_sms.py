import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def verify():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Test USSD Initial Menu
        print("\n--- Testing USSD Initial Menu ---")
        response = await ac.post(
            "/api/v1/ussd-sms/ussd",
            data={
                "sessionId": "session_123",
                "serviceCode": "*123#",
                "phoneNumber": "+2348012345678",
                "text": ""
            }
        )
        print(f"Response: {response.text}")
        assert "Welcome to NEMSAS" in response.text
        assert "CON" in response.text

        # 2. Test USSD Type Selection
        print("\n--- Testing USSD Type Selection ---")
        response = await ac.post(
            "/api/v1/ussd-sms/ussd",
            data={
                "sessionId": "session_123",
                "serviceCode": "*123#",
                "phoneNumber": "+2348012345678",
                "text": "1"
            }
        )
        print(f"Response: {response.text}")
        assert "location description" in response.text

        # 3. Test USSD Location Input
        print("\n--- Testing USSD Location Input ---")
        response = await ac.post(
            "/api/v1/ussd-sms/ussd",
            data={
                "sessionId": "session_123",
                "serviceCode": "*123#",
                "phoneNumber": "+2348012345678",
                "text": "1*Lekki Phase 1"
            }
        )
        print(f"Response: {response.text}")
        assert "Medical emergency at Lekki Phase 1" in response.text
        assert "Confirm?" in response.text

        # 4. Test USSD Final Confirmation
        print("\n--- Testing USSD Final Confirmation ---")
        response = await ac.post(
            "/api/v1/ussd-sms/ussd",
            data={
                "sessionId": "session_123",
                "serviceCode": "*123#",
                "phoneNumber": "+2348012345678",
                "text": "1*Lekki Phase 1*1"
            }
        )
        print(f"Response: {response.text}")
        assert "END Emergency reported" in response.text

        # 5. Test SMS Valid Format
        print("\n--- Testing SMS Valid Format ---")
        response = await ac.post(
            "/api/v1/ussd-sms/sms",
            data={
                "from": "+2348099998888",
                "to": "12345",
                "text": "EMERGENCY TRAUMA at Berger Bus Stop",
                "id": "sms_id_1",
                "date": "2026-04-13 14:00:00"
            }
        )
        print(f"Response: {response.json()}")
        assert response.json()["status"] == "success"
        assert "Ref:" in response.json()["message"]

        # 6. Test SMS Invalid Format (Help message)
        print("\n--- Testing SMS Invalid Format ---")
        response = await ac.post(
            "/api/v1/ussd-sms/sms",
            data={
                "from": "+2348099998888",
                "to": "12345",
                "text": "Help me my car crashed",
                "id": "sms_id_2",
                "date": "2026-04-13 14:05:00"
            }
        )
        print(f"Response: {response.json()}")
        assert "Invalid format" in response.json()["message"]

        # 7. Test Voice Callback
        print("\n--- Testing Voice Callback ---")
        response = await ac.post(
            "/api/v1/ussd-sms/voice",
            data={
                "sessionId": "voice_session_999",
                "isActive": "1",
                "callerNumber": "+2348077776666",
                "destinationNumber": "54321"
            }
        )
        print(f"Response XML: {response.text}")
        assert "<Response>" in response.text
        assert "Welcome to NEMSAS Emergency Service" in response.text
        assert "Reference:" in response.text

if __name__ == "__main__":
    asyncio.run(verify())
