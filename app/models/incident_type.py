from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base

class IncidentType(Base):
    __tablename__ = "incident_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)

    # Reverse relationship to Incident
    incidents = relationship("Incident", back_populates="incident_type")
