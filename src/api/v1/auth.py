from datetime import timedelta, datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.core import security
from src.core.config import settings
from src.db.base import get_db
from src.db.models.auth import AuthAction, TokenType
from src.schemas.user import Token, TokenPayload
from src.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, ActivateAccountRequest, Verify2FARequest, MessageResponse
from src.services.user import user_service
from src.services.auth import auth_service
from src.services.email import email_service
import jwt

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    request: Request,
    db: AsyncSession = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    ip_addr = request.client.host if request.client else None
    
    # 1. Fetch user directly to check lockout status
    user = await user_service.get_by_email(db, email=form_data.username)
    if not user:
        # Avoid email enumeration by still returning a generic error, but logging the attempt
        await auth_service.log_audit(db, AuthAction.LOGIN_FAILED, email_attempted=form_data.username, ip_address=ip_addr, details="Non-existent email")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    
    # 2. Check Lockout
    if user.lockout_until and user.lockout_until > datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail="Too many failed login attempts. Account locked for 15 minutes."
        )

    # 3. Check Credentials
    if not security.verify_password(form_data.password, user.hashed_password):
        locked_out = await auth_service.handle_failed_login(db, user, ip_address=ip_addr)
        await auth_service.log_audit(db, AuthAction.LOGIN_FAILED, user_id=user.id, email_attempted=user.email, ip_address=ip_addr, details="Incorrect password")
        if locked_out:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed login attempts. Account locked for 15 minutes.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    # 4. Check Activation Status
    if not user.is_active:
        await auth_service.log_audit(db, AuthAction.LOGIN_FAILED, user_id=user.id, email_attempted=user.email, ip_address=ip_addr, details="Inactive user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # 5. Success
    await auth_service.reset_failed_logins(db, user)
    await auth_service.log_audit(db, AuthAction.LOGIN_SUCCESS, user_id=user.id, email_attempted=user.email, ip_address=ip_addr)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(user.id, expires_delta=access_token_expires),
        "refresh_token": security.create_refresh_token(user.id),
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using a refresh token
    """
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.type != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")
    
    user = await user_service.get_by_id(db, user_id=int(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(user.id, expires_delta=access_token_expires),
        "refresh_token": security.create_refresh_token(user.id), # Refresh token rotation
        "token_type": "bearer",
    }

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Initiate a password reset flow. Returns a generic message whether the email exists or not.
    """
    user = await user_service.get_by_email(db, email=body.email)
    ip_addr = request.client.host if request.client else None

    if user and user.is_active:
        token = await auth_service.create_token(db, user.id, TokenType.RESET, expires_in_minutes=10)
        await auth_service.log_audit(db, AuthAction.PASSWORD_RESET_REQUEST, user_id=user.id, email_attempted=user.email, ip_address=ip_addr)
        
        # Send actual email
        await email_service.send_password_reset_otp(user.email, token.token)
    
    return {"message": "If the email is registered and active, a password reset OTP has been sent."}

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Submit OTP to reset password.
    """
    user = await auth_service.verify_and_use_token(db, body.otp, TokenType.RESET)
    ip_addr = request.client.host if request.client else None

    if not user or user.email != body.email:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Update password
    user.hashed_password = security.get_password_hash(body.new_password)
    await db.commit()

    await auth_service.log_audit(db, AuthAction.PASSWORD_RESET_SUCCESS, user_id=user.id, email_attempted=user.email, ip_address=ip_addr)

    return {"message": "Password has been successfully reset. Please log in again."}

@router.post("/activate", response_model=MessageResponse)
async def activate_account(
    request: Request,
    body: ActivateAccountRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Activate a newly created account using the secure token and set a password.
    """
    user = await auth_service.verify_and_use_token(db, body.token, TokenType.ACTIVATION)
    ip_addr = request.client.host if request.client else None

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired activation link")

    user.hashed_password = security.get_password_hash(body.password)
    user.is_active = True
    await db.commit()

    await auth_service.log_audit(db, AuthAction.ACCOUNT_ACTIVATION, user_id=user.id, email_attempted=user.email, ip_address=ip_addr)

    return {"message": "Account activated successfully. You may now log in."}

@router.post("/verify-partner-2fa", response_model=MessageResponse)
async def verify_partner_2fa(
    body: Verify2FARequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify the 2FA OTP sent during partner registration.
    """
    user = await auth_service.verify_and_use_token(db, body.otp, TokenType.TWO_FACTOR)
    if not user or user.email != body.email:
        raise HTTPException(status_code=400, detail="Invalid or expired 2FA OTP")

    # Mark user as active after 2FA validation
    user.is_active = True
    await db.commit()
    
    return {"message": "2FA verification successful. Account is now completely registered."}
