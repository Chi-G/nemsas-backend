from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import List, Optional
import enum

class PledgeStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    PARTIALLY_FULFILLED = "Partially Fulfilled"
    FULFILLED = "Fulfilled"
    REJECTED = "Rejected"

class FacilityRequestStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Partner(Base):
    __tablename__ = "partners"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    organisation_name: Mapped[str] = mapped_column(String(255))
    contact_person: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(500))
    
    is_verified: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    user: Mapped["User"] = relationship()
    pledges: Mapped[List["Pledge"]] = relationship(back_populates="partner")

class Pledge(Base):
    __tablename__ = "pledges"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"))
    ambulance_count: Mapped[int] = mapped_column(Integer)
    target_state_id: Mapped[Optional[int]] = mapped_column(Integer)
    target_lga_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    status: Mapped[PledgeStatus] = mapped_column(SQLAlchemyEnum(PledgeStatus), default=PledgeStatus.PENDING)
    fulfilled_count: Mapped[int] = mapped_column(default=0)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    partner: Mapped[Partner] = relationship(back_populates="pledges")

class Facility(Base):
    __tablename__ = "facilities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    facility_type: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    state_id: Mapped[int] = mapped_column(index=True)
    lga_id: Mapped[int] = mapped_column(index=True)
    
    is_active: Mapped[bool] = mapped_column(default=True)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class FacilityRequest(Base):
    __tablename__ = "facility_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"))
    facility_name: Mapped[str] = mapped_column(String(255))
    facility_type: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    state_id: Mapped[int] = mapped_column(index=True)
    lga_id: Mapped[int] = mapped_column(index=True)
    
    status: Mapped[FacilityRequestStatus] = mapped_column(SQLAlchemyEnum(FacilityRequestStatus), default=FacilityRequestStatus.PENDING)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
