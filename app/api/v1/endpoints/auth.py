from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.token import Token, LoginRequest, TokenRefreshRequest
from app.schemas.user import ChangePasswordRequest

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    *,
    db: AsyncSession = Depends(get_db),
    login_data: LoginRequest
) -> Any:
    """
    Login with email and password in JSON body
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = security.create_access_token(user.id, role=user.user_type, state_id=user.state_id)
    refresh_token = security.create_refresh_token(user.id, role=user.user_type, state_id=user.state_id)
    
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_expires_in = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "status": "success",
        "message": "Login successful",
        "expires_in": expires_in,
        "refresh_expires_in": refresh_expires_in
    }

@router.post("/refresh", response_model=Token)
async def refresh(
    *,
    db: AsyncSession = Depends(get_db),
    refresh_data: TokenRefreshRequest
) -> Any:
    """
    Refresh access and refresh tokens using a valid refresh token.
    """
    payload = security.verify_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
        
    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
        )
        
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
        
    access_token = security.create_access_token(user.id, role=user.user_type, state_id=user.state_id)
    new_refresh_token = security.create_refresh_token(user.id, role=user.user_type, state_id=user.state_id)
    
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_expires_in = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "status": "success",
        "message": "Token successfully refreshed",
        "expires_in": expires_in,
        "refresh_expires_in": refresh_expires_in
    }

@router.post("/change-password")
async def change_password(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    password_data: ChangePasswordRequest
) -> Any:
    """
    Change password for the currently authenticated user
    """
    if not security.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    hashed_password = security.get_password_hash(password_data.new_password)
    
    # Update user's password and status
    current_user.hashed_password = hashed_password
    current_user.is_password_changed = True
    
    db.add(current_user)
    await db.commit()
    
    return {
        "success": True,
        "message": "Password successfully changed"
    }
