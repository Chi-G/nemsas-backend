import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Date, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime, timezone

class IncidentStatus(str, enum.Enum):
    CREATED = "Created"
    Reported = "Reported"
    DISPATCHED = "Dispatched"
    ACCEPTED = "Accepted"
    EN_ROUTE = "En Route"
    AT_SCENE = "At Scene"
    PATIENT_LOADED = "Patient Loaded"
    EN_ROUTE_TO_ETC = "En Route to ETC"
    ARRIVED_AT_ETC = "Arrived at ETC"
    COMPLETED = "Completed"
    CLOSED = "Closed"

class ComplianceRating(str, enum.Enum):
    COMPLIANT = "Compliant"
    PARTIALLY_COMPLIANT = "Partially Compliant"
    NON_COMPLIANT = "Non-Compliant"

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
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)

    etc_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"), nullable=True)

    # Relationships
    dispatcher = relationship("User", foreign_keys=[dispatcher_id])
    hospital = relationship("Hospital", foreign_keys=[etc_id])
    ambulance = relationship("Ambulance", foreign_keys=[ambulance_id])
    incident_type = relationship("IncidentType", back_populates="incidents")
    state = relationship("State")
    
    status_history = relationship("IncidentStatusHistory", back_populates="incident")
    dispatches = relationship("Dispatch", back_populates="incident")
    claims = relationship("Claim", back_populates="incident")
    patients = relationship("Patient", back_populates="incident")

class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"
    
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    status = Column(SQLAlchemyEnum(IncidentStatus, native_enum=False))
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Link changed_by to modern UUID User
    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(String(255), nullable=True)
    
    incident = relationship("Incident", back_populates="status_history")
    changed_by = relationship("User")

class QAFinding(Base):
    __tablename__ = "qa_findings"
    
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    compliance_rating = Column(SQLAlchemyEnum(ComplianceRating, native_enum=False))
    findings_text = Column(String(1000))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Link officer to modern UUID User
    qa_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    incident = relationship("Incident")
    qa_officer = relationship("User")
