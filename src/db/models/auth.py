from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import Optional
import enum

class AuthAction(str, enum.Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
    PASSWORD_RESET_SUCCESS = "PASSWORD_RESET_SUCCESS"
    ACCOUNT_ACTIVATION = "ACCOUNT_ACTIVATION"
    ACCOUNT_LOCKOUT = "ACCOUNT_LOCKOUT"

class TokenType(str, enum.Enum):
    RESET = "RESET"
    TWO_FACTOR = "TWO_FACTOR"
    ACTIVATION = "ACTIVATION"

class AuthAuditLog(Base):
    __tablename__ = "auth_audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id")) # Nullable in case of failed login for non-existent email
    email_attempted: Mapped[Optional[str]] = mapped_column(String(255))
    action: Mapped[AuthAction] = mapped_column(SQLAlchemyEnum(AuthAction))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    details: Mapped[Optional[str]] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class UserToken(Base):
    __tablename__ = "user_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(255), index=True)
    token_type: Mapped[TokenType] = mapped_column(SQLAlchemyEnum(TokenType))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user = relationship("User", backref="tokens")
