from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    do_b = Column(Date, nullable=True)
    sex = Column(Integer, nullable=True) # Changed from String to Integer
    phone_number = Column(String(20), nullable=True)
    
    nhia = Column(String(50), nullable=True) # National Health Insurance Authority ID
    address = Column(String(500), nullable=True)
    
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    ambulance_id = Column(Integer, nullable=True) # Can map to Ambulance.id if needed
    etc_id = Column(Integer, nullable=True) # Emergency Treatment Center ID
    
    medical_interventions = Column(JSON, nullable=True)
    notes = Column(JSON, nullable=True) # Changed from String to JSON
    drugs = Column(JSON, nullable=True)
    runsheet = Column(String(255), nullable=True)
    extra_details = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    incident = relationship("Incident")
    claims = relationship("Claim", back_populates="patient")
    interventions = relationship("MedicalIntervention", back_populates="patient")
