from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    caller_name = Column(String, nullable=True)
    caller_number = Column(String, nullable=True)
    incident_date = Column(Date, nullable=True)
    incident_time = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    triage_category = Column(String, nullable=True)
    incident_location = Column(String, nullable=True)
    district_ward = Column(String, nullable=True)
    street = Column(String, nullable=True)
    area_council = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    incident_category_id = Column(Integer, ForeignKey("incident_types.id"), nullable=True)
    can_resolve_without_ambulance = Column(Boolean, nullable=True)
    treatment_center = Column(String, nullable=True)
    dispatch_full_name = Column(String, nullable=True)
    dispatcher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dispatch_date = Column(Date, nullable=True)
    supervisor_first_name = Column(String, nullable=True)
    supervisor_middle_name = Column(String, nullable=True)
    supervisor_last_name = Column(String, nullable=True)
    supervisor_date = Column(Date, nullable=True)
    serial_no = Column(String, unique=True, index=True, nullable=True)
    caller_is_patient = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    mass_casualty = Column(Boolean, default=False)
    total_patients = Column(Integer, nullable=True)

    ambulance_start = Column(DateTime(timezone=True), nullable=True)
    ambulance_stop = Column(DateTime(timezone=True), nullable=True)
    date_stop = Column(DateTime(timezone=True), nullable=True)
    incident_status_type = Column(String, nullable=True)
    event_status_type = Column(String, nullable=True)
    claims_approved = Column(String, nullable=True)
    state_name = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)

    etc_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"), nullable=True)

    # Relationships
    dispatcher = relationship("User", foreign_keys=[dispatcher_id])
    hospital = relationship("Hospital", foreign_keys=[etc_id])
    ambulance = relationship("Ambulance", foreign_keys=[ambulance_id])
    incident_type = relationship("IncidentType", back_populates="incidents")
