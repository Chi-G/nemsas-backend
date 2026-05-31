from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base

class EtcIntervention(Base):
    __tablename__ = "etc_interventions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    drug_id = Column(Integer, nullable=True)
    medical_intervention = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    dose = Column(Float, nullable=True)
    diagnosis = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    ambulance_id = Column(Integer, nullable=True)
    emergency_treatment_center_id = Column(Integer, nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)
    is_old = Column(Boolean, default=False, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="etc_interventions")
    patient = relationship("Patient", back_populates="etc_interventions")
