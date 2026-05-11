from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Enum as SQLAlchemyEnum, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone
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
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    organisation_name = Column(String(255))
    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User")
    pledges = relationship("Pledge", back_populates="partner")

class Pledge(Base):
    __tablename__ = "pledges"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    ambulance_count = Column(Integer, default=0)
    target_state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    target_lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    
    status = Column(SQLAlchemyEnum(PledgeStatus, native_enum=False), default=PledgeStatus.PENDING)
    fulfilled_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    partner = relationship("Partner", back_populates="pledges")
    target_state = relationship("State")
    target_lga = relationship("LGA")

class FacilityRequest(Base):
    __tablename__ = "facility_requests"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    facility_name = Column(String(255))
    facility_type = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    
    status = Column(SQLAlchemyEnum(FacilityRequestStatus, native_enum=False), default=FacilityRequestStatus.PENDING)
    rejection_reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    partner = relationship("Partner")
    state = relationship("State")
    lga = relationship("LGA")
