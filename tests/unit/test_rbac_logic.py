import pytest
from fastapi import HTTPException
from src.core.rbac import Permission as PermissionEnum, RoleName
from src.db.models.user import User, Role, Permission
from src.api import deps
from unittest.mock import MagicMock

@pytest.fixture
def real_user_setup():
    """
    Creates a real User model instance with a Role and Permissions for accurate attribute access.
    No database interaction is required for these unit tests.
    """
    user = User()
    user.is_active = True
    user.id = 1
    
    # Setup Role
    role = Role(name=RoleName.SEMSAS_ADMIN.value)
    
    # Setup Permissions using the official names from PermissionEnum
    # deps.py expects permission objects with a .name attribute
    perm_read = Permission(name="INCIDENT_READ")
    role.permissions = [perm_read]
    
    user.role = role
    user.state_id = 10
    return user

def test_permission_checker_success(real_user_setup):
    """Verifies that a user with the required permission passes the check."""
    # Note: deps.PermissionChecker takes a list of permission names (strings)
    checker = deps.PermissionChecker(["INCIDENT_READ"])
    # Should not raise any exception
    checker(current_user=real_user_setup)

def test_permission_checker_fail(real_user_setup):
    """Verifies that a user without the required permission is rejected with 403."""
    checker = deps.PermissionChecker(["INCIDENT_CREATE"])
    with pytest.raises(HTTPException) as exc:
        checker(current_user=real_user_setup)
    assert exc.value.status_code == 403

def test_role_checker_success(real_user_setup):
    """Verifies that a user with the allowed role passes the check."""
    # RoleChecker takes a list of allowed role names (strings)
    checker = deps.RoleChecker([RoleName.SEMSAS_ADMIN.value])
    checker(current_user=real_user_setup)

def test_role_checker_fail(real_user_setup):
    """Verifies that a user with a different role is rejected with 403."""
    checker = deps.RoleChecker([RoleName.NEMSAS_ADMIN.value])
    with pytest.raises(HTTPException) as exc:
        checker(current_user=real_user_setup)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_get_state_scope_semsas_admin(real_user_setup):
    """Verifies that SEMSAS Admin is scoped to their assigned state."""
    scope = await deps.get_state_scope(current_user=real_user_setup)
    assert scope == 10

@pytest.mark.asyncio
async def test_get_state_scope_global_admin(real_user_setup):
    """Verifies that NEMSAS Admin (Super Admin) has no state scope (None)."""
    real_user_setup.role.name = RoleName.NEMSAS_ADMIN.value
    scope = await deps.get_state_scope(current_user=real_user_setup)
    assert scope is None

@pytest.mark.asyncio
async def test_read_only_enforcement_get_success(real_user_setup):
    """Verifies that read-only roles can still perform GET requests."""
    real_user_setup.role.name = RoleName.VIEW_ONLY.value
    
    class MockRequest:
        method = "GET"
        
    # Should pass
    result = await deps.get_current_active_user(current_user=real_user_setup, request=MockRequest())
    assert result == real_user_setup

@pytest.mark.asyncio
async def test_read_only_enforcement_post_fail(real_user_setup):
    """Verifies that read-only roles are blocked from POST requests with 403."""
    real_user_setup.role.name = RoleName.VIEW_ONLY.value
    
    class MockRequest:
        method = "POST"
        
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_active_user(current_user=real_user_setup, request=MockRequest())
    assert exc.value.status_code == 403
