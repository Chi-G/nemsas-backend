from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class TransferForm(Base):
    __tablename__ = "transfer_forms"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    medic_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    hospice_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)  # Legacy
    patient_ids = Column(JSON, nullable=True) # Replaces patient_id to support multiple patients
    etc_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    run_sheet_id = Column(Integer, ForeignKey("run_sheets.id"), nullable=False, index=True)
    approve = Column(Boolean, default=False, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    incident = relationship("Incident")
    medic_user = relationship("User", foreign_keys=[medic_user_id])
    hospice_user = relationship("User", foreign_keys=[hospice_user_id])
    patient = relationship("Patient")
    hospital = relationship("Hospital", foreign_keys=[etc_id])
    run_sheet = relationship("RunSheet")
