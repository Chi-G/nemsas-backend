from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone
import enum
import uuid

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

class EmergencyType(str, enum.Enum):
    MEDICAL = "Medical"
    TRAUMA = "Trauma"
    OBSTETRIC = "Obstetric"
    PEDIATRIC = "Pediatric"
    OTHER = "Other"

class IncidentChannel(str, enum.Enum):
    APP = "App"
    USSD = "USSD"
    SMS = "SMS"
    CALL = "Call"
    DISPATCHER = "Dispatcher"

class ComplianceRating(str, enum.Enum):
    COMPLIANT = "Compliant"
    PARTIALLY_COMPLIANT = "Partially Compliant"
    NON_COMPLIANT = "Non-Compliant"

class Incident(Base):
    __tablename__ = "incidents"
    
    # Identifiers
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())) 
    serial_no = Column(String(100), nullable=True, index=True)
    
    # Location & Addressing
    location_label = Column(String(255), nullable=True) # maps to incidentLocation
    street = Column(String(255), nullable=True)
    district_ward = Column(String(255), nullable=True)
    area_council = Column(String(255), nullable=True)
    zip_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    
    # Caller Info
    caller_name = Column(String(255), nullable=True)
    caller_phone = Column(String(20), nullable=True) # maps to callerNumber
    caller_is_patient = Column(String(10), nullable=True) # maps to callerIsPatient ("Yes"/"No")
    
    # Classification & Severity
    incident_category = Column(String(100), nullable=True)
    triage_category = Column(String(50), nullable=True)
    emergency_type = Column(SQLAlchemyEnum(EmergencyType, native_enum=False), nullable=True) # back compat
    severity = Column(String(50), nullable=True)
    
    # Details
    description = Column(String(1000), nullable=True)
    recommendation = Column(String(1000), nullable=True)
    notes = Column(String(1000), nullable=True) # generic fallback notes
    
    # Resolution Capability
    can_resolve_without_ambulance = Column(Boolean, nullable=True)
    treatment_center = Column(String(255), nullable=True)
    referral_hospital_name = Column(String(255), nullable=True)
    hand_over_note = Column(String(1000), nullable=True)
    
    # Counters
    mass_casualty = Column(Boolean, default=False)
    total_patients = Column(Integer, nullable=True)
    patient_count = Column(Integer, default=1) # legacy field
    
    # Flow timestamps
    incident_date = Column(String(50), nullable=True) # original payload stores as String usually, can parse from created_at but explicitly storing is safer
    incident_time = Column(String(50), nullable=True)
    
    dispatch_date = Column(String(50), nullable=True)
    ambulance_start = Column(DateTime(timezone=True), nullable=True)
    ambulance_stop = Column(DateTime(timezone=True), nullable=True)
    etc_start = Column(DateTime(timezone=True), nullable=True)
    etc_stop = Column(DateTime(timezone=True), nullable=True)
    treatment_stop = Column(DateTime(timezone=True), nullable=True)
    
    resolved = Column(Boolean, default=False)
    time_resolved = Column(DateTime(timezone=True), nullable=True)
    
    # Status & Governance
    status = Column(SQLAlchemyEnum(IncidentStatus, native_enum=False), default=IncidentStatus.CREATED)
    channel = Column(SQLAlchemyEnum(IncidentChannel, native_enum=False), default=IncidentChannel.APP)
    location_confirmed = Column(Boolean, default=True)
    
    # Dispatch / Supervisor attribution
    dispatcher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dispatch_full_name = Column(String(255), nullable=True)
    
    # Point destination to hospital instead of User, and make sure it's an Integer
    destination_hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    
    # System Dates (Matching dataAdded/updatedAt keys)
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    added_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) # Legacy internal system use
    
    # Relationships
    status_history = relationship("IncidentStatusHistory", back_populates="incident")
    dispatches = relationship("Dispatch", back_populates="incident")
    dispatcher = relationship("User", foreign_keys=[dispatcher_id])
    state = relationship("State")
    lga = relationship("LGA")
    ward = relationship("Ward")
    destination_hospital = relationship("Hospital")
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
