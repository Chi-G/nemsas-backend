from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import List, Optional
import enum

class RunSheetStatus(str, enum.Enum):
    DRAFT = "Draft"
    CREW_SIGNED = "Awaiting ETC Co-Signature"
    FULLY_SIGNED = "Fully Co-Signed"

class RunSheet(Base):
    __tablename__ = "run_sheets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    dispatch_id: Mapped[int] = mapped_column(ForeignKey("dispatches.id"), index=True)
    
    # Patient Info
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Clinical Data
    chief_complaint: Mapped[Optional[str]] = mapped_column(String(1000))
    assessment: Mapped[Optional[str]] = mapped_column(String(2000))
    
    # Vitals
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(20)) # e.g. 120/80
    pulse_rate: Mapped[Optional[int]] = mapped_column(Integer)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer)
    oxygen_saturation: Mapped[Optional[float]] = mapped_column(Float)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    gcs: Mapped[Optional[int]] = mapped_column(Integer)
    
    status: Mapped[RunSheetStatus] = mapped_column(SQLAlchemyEnum(RunSheetStatus), default=RunSheetStatus.DRAFT)
    
    # Signatures
    crew_signature_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    crew_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    etc_signature_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    etc_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    # Relationships
    incident: Mapped["Incident"] = relationship()
    dispatch: Mapped["Dispatch"] = relationship()
    drug_entries: Mapped[List["RunSheetDrugEntry"]] = relationship(back_populates="run_sheet")

class RunSheetDrugEntry(Base):
    __tablename__ = "run_sheet_drug_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    run_sheet_id: Mapped[int] = mapped_column(ForeignKey("run_sheets.id"), index=True)
    
    drug_id: Mapped[Optional[int]] = mapped_column(ForeignKey("drugs.id"), nullable=True)
    custom_drug_name: Mapped[Optional[str]] = mapped_column(String(255))
    dosage: Mapped[str] = mapped_column(String(255))
    administered_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_reimbursable: Mapped[bool] = mapped_column(default=True)
    
    run_sheet: Mapped[RunSheet] = relationship(back_populates="drug_entries")

class RunSheetHistory(Base):
    __tablename__ = "run_sheet_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    run_sheet_id: Mapped[int] = mapped_column(ForeignKey("run_sheets.id"), index=True)
    
    data_snapshot: Mapped[dict] = mapped_column(JSON)
    saved_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    saved_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
