from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import List, Optional
import enum

class AmbulanceStatus(str, enum.Enum):
    ACTIVE = "Active"
    UNDER_MAINTENANCE = "Under Maintenance"
    OFFLINE = "Offline"
    DECOMMISSIONED = "Decommissioned"
    ON_DUTY = "On Duty" # Currently assigned to an incident

class AccreditationType(str, enum.Enum):
    BLS = "BLS"
    ALS = "ALS"

class Ambulance(Base):
    __tablename__ = "ambulances"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    make_model: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(Integer)
    accreditation_type: Mapped[AccreditationType] = mapped_column(SQLAlchemyEnum(AccreditationType))
    fuel_type: Mapped[Optional[str]] = mapped_column(String(50))
    capacity: Mapped[int] = mapped_column(default=1)
    
    status: Mapped[AmbulanceStatus] = mapped_column(SQLAlchemyEnum(AmbulanceStatus), default=AmbulanceStatus.ACTIVE)
    is_paused: Mapped[bool] = mapped_column(default=False)
    
    # Location
    last_latitude: Mapped[Optional[float]] = mapped_column(Float)
    last_longitude: Mapped[Optional[float]] = mapped_column(Float)
    state_id: Mapped[int] = mapped_column(index=True)
    lga_id: Mapped[int] = mapped_column(index=True)
    
    partner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id")) # Fleet Owner / ETP / Partner
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), 
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

class Dispatch(Base):
    __tablename__ = "dispatches"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    ambulance_id: Mapped[int] = mapped_column(ForeignKey("ambulances.id"))
    crew_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    dispatch_timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    accepted_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    incident: Mapped["Incident"] = relationship(back_populates="dispatches")
    ambulance: Mapped[Ambulance] = relationship()

class GPSHistory(Base):
    __tablename__ = "gps_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ambulance_id: Mapped[int] = mapped_column(ForeignKey("ambulances.id"))
    incident_id: Mapped[Optional[int]] = mapped_column(ForeignKey("incidents.id"))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_paused: Mapped[bool] = mapped_column(default=False)
