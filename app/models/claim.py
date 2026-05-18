from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone
import enum

class ClaimStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PAID = "Paid"

class ClaimType(str, enum.Enum):
    AMBULANCE = "Ambulance"
    ETC = "ETC"

class ClaimAction(str, enum.Enum):
    APPROVE = "Approve"
    REJECT = "Reject"

class ETCIntake(Base):
    __tablename__ = "etc_intakes"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), unique=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True) # Connect to specific hospital
    
    arrival_time = Column(DateTime(timezone=True))
    initial_assessment = Column(String(1000), nullable=True)
    triage_category = Column(String(50), nullable=True)
    interventions = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    incident = relationship("Incident")
    hospital = relationship("Hospital")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), index=True, nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True, nullable=True)
    
    # Submission Meta
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) 
    claim_type: str | None = Column(SQLAlchemyEnum(ClaimType, native_enum=False), nullable=True)  # type: ignore
    
    # Descriptive Fields
    title = Column(String(255), nullable=True)
    patient_name = Column(String(255), nullable=True)
    ambulance_type = Column(String(50), nullable=True)
    incident_category = Column(String(100), nullable=True)
    
    # Logistical context
    nhia = Column(String(100), nullable=True) # Healthcare scheme name
    location = Column(String(255), nullable=True)
    service_provider = Column(String(255), nullable=True)
    incident_date = Column(String(50), nullable=True)
    
    # Financials / Metrics
    distance_covered = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True) # Backcompat
    
    total_price = Column(Float, default=0.0)
    amount = Column(Float, default=0.0) # Backcompat
    
    # Reviews & Resolutions
    review = Column(String(500), nullable=True) # Holds codes like "Incorrect diagnosis", "Duplicate claim"
    etc_review = Column(String(500), nullable=True)
    
    status = Column(String(50), default="New") # Standardizing on string status to exactly mirror "New", "Approved", etc.
    rejection_reason = Column(String(255), nullable=True)
    
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    incident = relationship("Incident", back_populates="claims")
    patient = relationship("Patient", back_populates="claims")
    submitting_user = relationship("User", foreign_keys=[user_id])
    processor = relationship("User", foreign_keys=[processed_by_id])
    images = relationship("ClaimImage", back_populates="claim")

class ClaimAuditLog(Base):
    __tablename__ = "claim_audit_logs"
    
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    action = Column(SQLAlchemyEnum(ClaimAction, native_enum=False))
    # Link to UUID User
    processed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    claim = relationship("Claim")
    processor = relationship("User", foreign_keys=[processed_by_id])

class ClaimImage(Base):
    __tablename__ = "claim_images"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    claim_id = Column(Integer, ForeignKey("claims.id"), index=True, nullable=True)
    claim_title = Column(String(500), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), index=True, nullable=True)
    image_url = Column(String(1000), nullable=True)
    is_etc = Column(Boolean, default=False)
    
    # Relationships
    claim = relationship("Claim", back_populates="images")
    incident = relationship("Incident")

