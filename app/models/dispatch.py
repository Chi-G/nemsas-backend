from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float, Enum as SQLAlchemyEnum, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone
import enum

class IncidentLeg(str, enum.Enum):
    DISPATCH_TO_SCENE = "dispatch_to_scene"
    SCENE_TO_ETC = "scene_to_etc"
    OFFLINE = "offline"

class Dispatch(Base):
    __tablename__ = "dispatches"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"))
    # User foreign key is UUID
    crew_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    dispatch_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    accepted_timestamp = Column(DateTime(timezone=True), nullable=True)
    completed_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    total_distance = Column(Float, default=0.0)
    
    incident = relationship("Incident", back_populates="dispatches")
    ambulance = relationship("Ambulance")
    crew = relationship("User")

class GPSHistory(Base):
    __tablename__ = "gps_history"
    
    id = Column(Integer, primary_key=True)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"))
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_paused = Column(Boolean, default=False)
    
    incident_leg = Column(SQLAlchemyEnum(IncidentLeg, native_enum=False), nullable=True)
    delta_distance = Column(Float, default=0.0)
    
    ambulance = relationship("Ambulance")
    incident = relationship("Incident")
