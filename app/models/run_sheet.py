from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum, JSON, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone
import enum

class RunSheetStatus(str, enum.Enum):
    DRAFT = "Draft"
    CREW_SIGNED = "Awaiting ETC Co-Signature"
    FULLY_SIGNED = "Fully Co-Signed"

class RunSheet(Base):
    __tablename__ = "run_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), index=True, nullable=True)
    dispatch_id = Column(Integer, ForeignKey("dispatches.id"), index=True, nullable=True)
    
    # Linking Identity Context
    title = Column(String(255), nullable=True) # Maps to titles in payload
    patient_id = Column(JSON, nullable=True)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"), index=True, nullable=True)
    emergency_treatment_center_id = Column(Integer, ForeignKey("hospitals.id"), index=True, nullable=True)
    price = Column(Float, nullable=True)
    
    # Logistics Routing
    route_from = Column(String(255), nullable=True)
    route_to = Column(String(255), nullable=True)
    take_off_time = Column(DateTime(timezone=True), nullable=True)
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    total_minutes_to_hospital = Column(Float, nullable=True)
    
    # User Assignments matching dynamic medic/hospice types
    medic_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    hospice_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Patient Info (legacy fields)
    patient_name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Clinical Data
    chief_complaint = Column(String(1000), nullable=True)
    assessment = Column(String(2000), nullable=True)
    
    # Vitals
    blood_pressure = Column(String(20), nullable=True)
    pulse_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    gcs = Column(Integer, nullable=True)
    
    status = Column(SQLAlchemyEnum(RunSheetStatus, native_enum=False), default=RunSheetStatus.DRAFT)
    
    # User Signatures linked to UUID users
    crew_signature_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    crew_signed_at = Column(DateTime(timezone=True), nullable=True)
    
    etc_signature_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    etc_signed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Data Audit Alignment
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    incident = relationship("Incident")
    dispatch = relationship("Dispatch")
    ambulance = relationship("Ambulance")
    emergency_treatment_center = relationship("Hospital")
    
    medic_user = relationship("User", foreign_keys=[medic_user_id])
    hospice_user = relationship("User", foreign_keys=[hospice_user_id])
    
    drug_entries = relationship("RunSheetDrugEntry", back_populates="run_sheet")
    crew_signer = relationship("User", foreign_keys=[crew_signature_id])
    etc_signer = relationship("User", foreign_keys=[etc_signature_id])

class RunSheetDrugEntry(Base):
    __tablename__ = "run_sheet_drug_entries"
    
    id = Column(Integer, primary_key=True)
    run_sheet_id = Column(Integer, ForeignKey("run_sheets.id"), index=True)
    
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True)
    custom_drug_name = Column(String(255), nullable=True)
    dosage = Column(String(255))
    administered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_reimbursable = Column(Boolean, default=True)
    
    run_sheet = relationship("RunSheet", back_populates="drug_entries")
    drug = relationship("Drug")

class RunSheetHistory(Base):
    __tablename__ = "run_sheet_history"
    
    id = Column(Integer, primary_key=True)
    run_sheet_id = Column(Integer, ForeignKey("run_sheets.id"), index=True)
    
    data_snapshot = Column(JSON)
    saved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Linked to UUID User
    saved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    run_sheet = relationship("RunSheet")
    saved_by = relationship("User")
