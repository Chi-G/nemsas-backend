from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.db.models.auth import AuthAuditLog, AuthAction, UserToken, TokenType
from src.db.models.user import User
from src.core.security import get_password_hash
from datetime import datetime, timezone, timedelta
import random
import string
from typing import Optional

class AuthService:
    @staticmethod
    async def log_audit(
        db: AsyncSession, 
        action: AuthAction, 
        user_id: Optional[int] = None, 
        email_attempted: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[str] = None
    ):
        log = AuthAuditLog(
            user_id=user_id,
            email_attempted=email_attempted,
            action=action,
            ip_address=ip_address,
            details=details
        )
        db.add(log)
        await db.commit()

    @staticmethod
    async def handle_failed_login(db: AsyncSession, user: User, ip_address: Optional[str] = None):
        user.failed_login_attempts += 1
        locked_out = False
        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
            locked_out = True
            
        await db.commit()
        await db.refresh(user)

        if locked_out:
            await AuthService.log_audit(db, action=AuthAction.ACCOUNT_LOCKOUT, user_id=user.id, email_attempted=user.email, ip_address=ip_address, details="Account locked after 5 failed attempts")
        
        return locked_out

    @staticmethod
    async def reset_failed_logins(db: AsyncSession, user: User):
        if user.failed_login_attempts > 0 or user.lockout_until is not None:
            user.failed_login_attempts = 0
            user.lockout_until = None
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()

    @staticmethod
    async def generate_otp() -> str:
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    async def generate_secure_token() -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    @staticmethod
    async def create_token(db: AsyncSession, user_id: int, token_type: TokenType, expires_in_minutes: int) -> UserToken:
        token_str = await AuthService.generate_otp() if token_type in [TokenType.RESET, TokenType.TWO_FACTOR] else await AuthService.generate_secure_token()
        
        # Invalidate old tokens of this type for the user
        await db.execute(
            update(UserToken)
            .where(UserToken.user_id == user_id, UserToken.token_type == token_type, UserToken.is_used == False)
            .values(is_used=True)
        )

        user_token = UserToken(
            user_id=user_id,
            token=token_str,
            token_type=token_type,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=expires_in_minutes)
        )
        db.add(user_token)
        await db.commit()
        await db.refresh(user_token)
        return user_token

    @staticmethod
    async def verify_and_use_token(db: AsyncSession, token_str: str, token_type: TokenType) -> Optional[User]:
        result = await db.execute(
            select(UserToken).where(
                UserToken.token == token_str,
                UserToken.token_type == token_type,
                UserToken.is_used == False,
                UserToken.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        token = result.scalars().first()
        if not token:
            return None
            
        token.is_used = True
        
        user_res = await db.execute(select(User).where(User.id == token.user_id))
        user = user_res.scalars().first()
        
        await db.commit()
        return user

auth_service = AuthService()
