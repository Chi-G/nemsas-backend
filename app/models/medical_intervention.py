from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone

class MedicalIntervention(Base):
    __tablename__ = "medical_interventions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    is_alert = Column(Boolean, default=False)
    can_speak = Column(Boolean, default=False)
    is_in_pain = Column(Boolean, default=False)
    un_responsive = Column(Boolean, default=False)
    
    main_complaint = Column(String, nullable=True)
    primary_survey = Column(String, nullable=True)
    physical_examination_findings = Column(String, nullable=True)
    
    iv_fluid_type = Column(String, nullable=True)
    size_of_fluid = Column(String, nullable=True)
    location_of_iv_infusion = Column(String, nullable=True)
    total_iv_fluid_volume_given = Column(String, nullable=True)
    
    oxygen = Column(String, nullable=True)
    remarks = Column(String, nullable=True)
    
    pulse = Column(Integer, nullable=True)
    blood_pressure = Column(String, nullable=True)
    resp = Column(Integer, nullable=True)
    glucose = Column(Integer, nullable=True)
    sp02 = Column(Integer, nullable=True)
    
    notes = Column(String, nullable=True)
    medical_intervention_details = Column(String, nullable=True) # Mapping from mediicalIntervention in JSON
    
    incident_drugs = Column(JSON, nullable=True)
    
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    time_taken = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="interventions")
