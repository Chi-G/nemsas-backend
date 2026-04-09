from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.core.config import settings
from src.core.rbac import RoleName, is_read_only_role
from src.db.base import get_db
from src.db.models.user import User
from src.schemas.user import TokenPayload
from src.services.user import user_service

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
             raise jwt.PyJWTError()
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await user_service.get_by_id(db, user_id=int(token_data.sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    request: Request = None
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Global Read-Only Enforcement
    if request and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        if is_read_only_role(current_user.role.name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Read-only roles cannot perform write operations",
            )
            
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)):
        if current_user.role.name == RoleName.NEMSAS_ADMIN:
            return current_user
        if current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user

class PermissionChecker:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def __call__(self, current_user: User = Depends(get_current_active_user)):
        if current_user.role.name == RoleName.NEMSAS_ADMIN:
            return current_user
            
        user_permissions = [p.name for p in current_user.role.permissions]
        for perm in self.required_permissions:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
        return current_user

async def get_state_scope(
    current_user: User = Depends(get_current_active_user)
) -> Optional[int]:
    """
    Returns the state_id if the user's role is SEMSAS Admin.
    Returns None for NEMSAS Admin (Super Admin).
    """
    if current_user.role.name == RoleName.NEMSAS_ADMIN:
        return None
    if current_user.role.name == RoleName.SEMSAS_ADMIN:
        return current_user.state_id
    return None
