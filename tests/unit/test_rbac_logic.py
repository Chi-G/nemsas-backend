import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from src.core.rbac import Permission, RoleName
from src.db.models.user import User
from src.api import deps

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.is_active = True
    class MockRole:
        def __init__(self):
            self.name = ""
            self.permissions = []
    user.role = MockRole()
    user.state_id = 10
    return user

@pytest.mark.asyncio
async def test_permission_checker_success(mock_user):
    mock_user.role.permissions = [Permission.INCIDENT_CREATE]
    checker = deps.PermissionChecker([Permission.INCIDENT_CREATE])
    # Should not raise
    await checker(current_user=mock_user)

@pytest.mark.asyncio
async def test_permission_checker_fail(mock_user):
    mock_user.role.permissions = [Permission.INCIDENT_READ]
    checker = deps.PermissionChecker([Permission.INCIDENT_CREATE])
    with pytest.raises(HTTPException) as exc:
        await checker(current_user=mock_user)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_role_checker_success(mock_user):
    mock_user.role.name = RoleName.NEMSAS_ADMIN.value
    checker = deps.RoleChecker([RoleName.NEMSAS_ADMIN])
    # Should not raise
    await checker(current_user=mock_user)

@pytest.mark.asyncio
async def test_role_checker_fail(mock_user):
    mock_user.role.name = RoleName.CALL_CENTER_AGENT.value
    checker = deps.RoleChecker([RoleName.NEMSAS_ADMIN])
    with pytest.raises(HTTPException) as exc:
        await checker(current_user=mock_user)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_get_state_scope_semsas_admin(mock_user):
    mock_user.role.name = RoleName.SEMSAS_ADMIN.value
    scope = await deps.get_state_scope(current_user=mock_user)
    assert scope == 10

@pytest.mark.asyncio
async def test_get_state_scope_global_admin(mock_user):
    mock_user.role.name = RoleName.NEMSAS_ADMIN.value
    scope = await deps.get_state_scope(current_user=mock_user)
    assert scope is None

@pytest.mark.asyncio
async def test_read_only_enforcement_get_success(mock_user):
    mock_user.role.name = RoleName.VIEW_ONLY.value
    
    # GET request should pass
    class MockRequest:
        method = "GET"
        
    result = await deps.get_current_active_user(current_user=mock_user, request=MockRequest())
    assert result == mock_user

@pytest.mark.asyncio
async def test_read_only_enforcement_post_fail(mock_user):
    mock_user.role.name = RoleName.VIEW_ONLY.value
    
    # POST request should fail for read-only role
    class MockRequest:
        method = "POST"
        
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_active_user(current_user=mock_user, request=MockRequest())
    assert exc.value.status_code == 403
