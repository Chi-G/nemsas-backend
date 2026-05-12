from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class AmbulanceType(Base):
    __tablename__ = "ambulance_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    ambulances = relationship("Ambulance", back_populates="ambulance_type")
