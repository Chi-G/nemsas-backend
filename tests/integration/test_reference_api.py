import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.reference import Drug, AmbulanceType
import uuid

@pytest.mark.asyncio
async def test_admin_can_manage_drugs(client: AsyncClient, admin_token_headers, db: AsyncSession):
    # 1. Create Drug
    response = await client.post(
        "/api/v1/reference/drugs",
        json={"name": "New Audit Drug", "dosage_form": "Syrup", "is_nhia_approved": True},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    drug_id = response.json()["id"]

    # 2. Update Drug
    response = await client.patch(
        f"/api/v1/reference/drugs/{drug_id}",
        json={"name": "Updated Audit Drug"},
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Audit Drug"

@pytest.mark.asyncio
async def test_public_cannot_manage_reference(client: AsyncClient, db: AsyncSession):
    # Non-admin request
    response = await client.post(
        "/api/v1/reference/drugs",
        json={"name": "Illegal Drug"}
    )
    assert response.status_code == 401 # No token

@pytest.mark.asyncio
async def test_get_states_lgas_hierarchy(client: AsyncClient, db: AsyncSession):
    response = await client.get("/api/v1/reference/states-lgas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if len(response.json()) > 0:
        assert "lgas" in response.json()[0]
