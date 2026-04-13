from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import List, Optional
import enum

class IncidentStatus(str, enum.Enum):
    CREATED = "Created"
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

class Incident(Base):
    __tablename__ = "incidents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True) # Public/Primary linking key
    
    # Location
    location_label: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    state_id: Mapped[Optional[int]] = mapped_column(index=True, nullable=True)
    lga_id: Mapped[Optional[int]] = mapped_column(index=True, nullable=True)
    
    # Caller Info
    caller_name: Mapped[Optional[str]] = mapped_column(String(255))
    caller_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Emergency Details
    emergency_type: Mapped[EmergencyType] = mapped_column(SQLAlchemyEnum(EmergencyType))
    severity: Mapped[Optional[str]] = mapped_column(String(50))
    patient_count: Mapped[int] = mapped_column(default=1)
    notes: Mapped[Optional[str]] = mapped_column(String(1000))
    
    status: Mapped[IncidentStatus] = mapped_column(SQLAlchemyEnum(IncidentStatus), default=IncidentStatus.CREATED)
    channel: Mapped[IncidentChannel] = mapped_column(SQLAlchemyEnum(IncidentChannel), default=IncidentChannel.APP)
    location_confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    # Relationships
    status_history: Mapped[List["IncidentStatusHistory"]] = relationship(back_populates="incident")
    dispatches: Mapped[List["Dispatch"]] = relationship(back_populates="incident")

class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    status: Mapped[IncidentStatus] = mapped_column(SQLAlchemyEnum(IncidentStatus))
    changed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[Optional[str]] = mapped_column(String(255))
    
    incident: Mapped[Incident] = relationship(back_populates="status_history")

class QAFinding(Base):
    __tablename__ = "qa_findings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    compliance_rating: Mapped[str] = mapped_column(String(50)) # Compliant, Partially Compliant, Non-Compliant
    findings_text: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    qa_officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
