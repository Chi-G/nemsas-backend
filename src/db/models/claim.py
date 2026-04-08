from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import List, Optional
import enum

class ClaimStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PAID = "Paid"

class ClaimType(str, enum.Enum):
    AMBULANCE = "Ambulance"
    ETC = "ETC"

class RunSheet(Base):
    __tablename__ = "run_sheets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), unique=True)
    
    # Patient Data (Structured JSON for flexibility in care forms)
    patient_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Drugs Administered (List of dicts: {"drug_id": 1, "name": "...", "dose": "..."})
    drugs_administered: Mapped[Optional[list]] = mapped_column(JSON)
    
    # Signatures
    crew_signature: Mapped[Optional[str]] = mapped_column(String(255)) # Authenticated signature ID/Hash
    crew_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    crew_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    etc_signature: Mapped[Optional[str]] = mapped_column(String(255))
    etc_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    etc_staff_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    is_locked: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

class ETCIntake(Base):
    __tablename__ = "etc_intakes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), unique=True)
    etc_facility_id: Mapped[int] = mapped_column(ForeignKey("users.id")) # Hospital/ETC ID
    
    arrival_time: Mapped[datetime] = mapped_column(DateTime)
    initial_assessment: Mapped[str] = mapped_column(String(1000))
    triage_category: Mapped[str] = mapped_column(String(50))
    interventions: Mapped[Optional[str]] = mapped_column(String(1000))
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class Claim(Base):
    __tablename__ = "claims"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) # Submitting user (Crew or ETC)
    claim_type: Mapped[ClaimType] = mapped_column(SQLAlchemyEnum(ClaimType))
    
    amount: Mapped[float] = mapped_column(Float)
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    
    status: Mapped[ClaimStatus] = mapped_column(SQLAlchemyEnum(ClaimStatus), default=ClaimStatus.PENDING)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255))
    
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    processed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
