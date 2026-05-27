import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash

@pytest_asyncio.fixture
async def setup_role_test_data(db: AsyncSession):
    # Clean up roles and users to avoid unique constraints
    await db.execute(delete(User).where(User.email != "admin@test.com"))
    await db.execute(delete(Role).where(Role.id.in_(["TEST_ROLE_1", "TEST_ROLE_2", "NEW_ROLE"])))
    await db.commit()

    # Create test roles
    role1 = Role(id="TEST_ROLE_1", name="Test Role One")
    role2 = Role(id="TEST_ROLE_2", name="Test Role Two")
    db.add_all([role1, role2])
    await db.flush()

    # Create Superadmin
    superadmin = User(
        email="superadmin_role@example.com",
        first_name="Super",
        last_name="Admin",
        user_name="superadmin_role_test",
        hashed_password=get_password_hash("password123"),
        user_type="SUPERADMINISTRATOR",
        is_active=True
    )
    db.add(superadmin)

    # Create Regular User
    regular_user = User(
        email="regular_role@example.com",
        first_name="Regular",
        last_name="User",
        user_name="regular_role_test",
        hashed_password=get_password_hash("password123"),
        user_type="SEMSASUSER",
        is_active=True
    )
    db.add(regular_user)

    await db.commit()

    return {
        "superadmin": superadmin,
        "regular_user": regular_user,
        "role1": role1,
        "role2": role2
    }


@pytest.mark.asyncio
async def test_superadmin_can_manage_roles(
    client: AsyncClient, db: AsyncSession, setup_role_test_data, get_user_token_headers
):
    superadmin = setup_role_test_data["superadmin"]
    role1 = setup_role_test_data["role1"]
    
    headers = get_user_token_headers(superadmin)

    # 1. Create a Role
    create_payload = {
        "id": "NEW_ROLE",
        "name": "New Dynamic Role"
    }
    response = await client.post("/api/v1/roles/", json=create_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["id"] == "NEW_ROLE"
    assert response.json()["data"]["name"] == "New Dynamic Role"

    # Verify created in DB
    db_role_res = await db.execute(select(Role).where(Role.id == "NEW_ROLE"))
    db_role = db_role_res.scalars().first()
    assert db_role is not None

    # 2. Update a Role
    update_payload = {
        "name": "Updated Role Name"
    }
    response = await client.patch(f"/api/v1/roles/{role1.id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Role Name"

    # Verify updated in DB
    await db.refresh(role1)
    assert role1.name == "Updated Role Name"

    # 3. Delete a Role
    response = await client.delete(f"/api/v1/roles/{role1.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify deleted in DB
    db_deleted_res = await db.execute(select(Role).where(Role.id == role1.id))
    assert db_deleted_res.scalars().first() is None


@pytest.mark.asyncio
async def test_non_superadmin_cannot_write_roles(
    client: AsyncClient, db: AsyncSession, setup_role_test_data, get_user_token_headers
):
    regular_user = setup_role_test_data["regular_user"]
    role2 = setup_role_test_data["role2"]
    
    headers = get_user_token_headers(regular_user)

    # Try create
    response = await client.post("/api/v1/roles/", json={"id": "NEW_ROLE", "name": "Hack"}, headers=headers)
    assert response.status_code == 403

    # Try update
    response = await client.patch(f"/api/v1/roles/{role2.id}", json={"name": "Hack"}, headers=headers)
    assert response.status_code == 403

    # Try delete
    response = await client.delete(f"/api/v1/roles/{role2.id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_edit_delete_non_existent_role_returns_404(
    client: AsyncClient, setup_role_test_data, get_user_token_headers
):
    superadmin = setup_role_test_data["superadmin"]
    headers = get_user_token_headers(superadmin)

    # Try update non-existent
    response = await client.patch("/api/v1/roles/NON_EXISTENT", json={"name": "Hack"}, headers=headers)
    assert response.status_code == 404

    # Try delete non-existent
    response = await client.delete("/api/v1/roles/NON_EXISTENT", headers=headers)
    assert response.status_code == 404
