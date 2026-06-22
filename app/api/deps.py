from typing import AsyncGenerator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import SessionLocal, get_db
from app.models.user import User
from app.partners.models import PartnerUser
from app.schemas.token import TokenPayload

# Switched to HTTPBearer for a simple "Bearer <token>" input in Swagger
reusable_oauth2 = HTTPBearer()



async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> User:
    try:
        # HTTPBearer returns credentials.credentials as the token string
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    import uuid
    try:
        user_uuid = uuid.UUID(token_data.sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    result = await db.execute(
        select(User)
        .where(User.id == user_uuid)
        .options(
            selectinload(User.state),
            selectinload(User.lga),
            selectinload(User.ward),
            selectinload(User.partner)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user


async def get_current_partner_user(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> PartnerUser:
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    try:
        partner_user_id = int(token_data.sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Please ensure you are using a Partner token, not a normal User token.",
        )

    result = await db.execute(
        select(PartnerUser).where(PartnerUser.id == partner_user_id)
    )
    partner_user = result.scalar_one_or_none()
    
    if not partner_user:
        raise HTTPException(status_code=404, detail="Partner user not found")
    if not partner_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive partner user")
        
    return partner_user


class PermissionChecker:
    def __init__(self, allowed_roles: list[str] | None = None, allowed_users: list[str] | None = None):
        """
        Check if the current user has the required roles or is one of the allowed users.
        If both are provided, the user must satisfy AT LEAST one condition.
        If neither is provided, any authenticated user is allowed.
        """
        self.allowed_roles = allowed_roles
        self.allowed_users = allowed_users

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        is_allowed = False

        # If no restrictions are provided, allow all authenticated users
        if not self.allowed_roles and not self.allowed_users:
            is_allowed = True
        
        # Check roles
        if self.allowed_roles and current_user.user_type in self.allowed_roles:
            is_allowed = True
            
        # Check specific user IDs
        if self.allowed_users and str(current_user.id) in self.allowed_users:
            is_allowed = True

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user


async def get_current_any_user(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> any:
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    import uuid
    try:
        user_uuid = uuid.UUID(token_data.sub)
        result = await db.execute(
            select(User)
            .where(User.id == user_uuid)
            .options(
                selectinload(User.state),
                selectinload(User.lga),
                selectinload(User.ward),
                selectinload(User.partner)
            )
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        return user
    except (ValueError, TypeError):
        try:
            partner_id = int(token_data.sub)
            result = await db.execute(
                select(PartnerUser).where(PartnerUser.id == partner_id)
            )
            partner = result.scalar_one_or_none()
            if not partner or not partner.is_active:
                raise HTTPException(status_code=401, detail="Partner not found or inactive")
            return partner
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid token subject")


class PermissionCheckerAny:
    def __init__(self, allowed_roles: list[str] | None = None):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: any = Depends(get_current_any_user)) -> any:
        if not self.allowed_roles:
            return current_user
        if current_user.user_type in self.allowed_roles:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )



async def get_current_partner(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> any:
    from app.models.partner import Partner
    token_str = token.credentials
    
    # 1. Try to find the partner by the static token column in the database
    result = await db.execute(
        select(Partner)
        .where(Partner.token == token_str)
        .options(selectinload(Partner.user))
    )
    partner = result.scalar_one_or_none()
    
    # 2. If not found, try to decode it as a JWT and find by sub
    if not partner:
        try:
            payload = jwt.decode(
                token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            sub = payload.get("sub")
            if sub:
                import uuid
                # Check if sub is a UUID (user_id) or an integer (partner.id)
                try:
                    user_uuid = uuid.UUID(sub)
                    result = await db.execute(
                        select(Partner)
                        .where(Partner.user_id == user_uuid)
                        .options(selectinload(Partner.user))
                    )
                    partner = result.scalar_one_or_none()
                except ValueError:
                    # Try as integer partner ID
                    partner_id = int(sub)
                    result = await db.execute(
                        select(Partner)
                        .where(Partner.id == partner_id)
                        .options(selectinload(Partner.user))
                    )
                    partner = result.scalar_one_or_none()
        except Exception:
            pass
            
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate partner credentials",
        )
    return partner
