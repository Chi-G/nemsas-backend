from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import List, Optional

class State(Base):
    __tablename__ = "states"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    population: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    lgas: Mapped[List["LGA"]] = relationship(back_populates="state")

class LGA(Base):
    __tablename__ = "lgas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"))
    name: Mapped[str] = mapped_column(String(100), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    state: Mapped[State] = relationship(back_populates="lgas")

class Drug(Base):
    __tablename__ = "drugs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    dosage_form: Mapped[Optional[str]] = mapped_column(String(100))
    is_nhia_approved: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

class AmbulanceType(Base):
    __tablename__ = "ambulance_types"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

class AccreditationCategory(Base):
    __tablename__ = "accreditation_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

class SystemAuditLog(Base):
    __tablename__ = "system_audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(50), index=True)
    record_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20)) # CREATE, UPDATE, DEACTIVATE
    changes: Mapped[Optional[dict]] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
