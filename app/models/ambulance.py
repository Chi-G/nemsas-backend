from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=True)
    ambulance_type_id = Column(Integer, ForeignKey("ambulance_types.id"), nullable=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    nhia_or_shia = Column(String, nullable=True)
    service_type = Column(String, nullable=True)
    online = Column(Boolean, default=True)
    driver_name = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    state_name = Column(String, nullable=True)
    event_status_type = Column(String, nullable=True)
    plate_number = Column(String, nullable=True)
    make = Column(String, nullable=True)
    year = Column(String, nullable=True)
    model = Column(String, nullable=True)
    accreditation_type = Column(String, nullable=True)
    vehicle_ownership_type = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now())



    # Relationships
    ambulance_type = relationship("AmbulanceType", back_populates="ambulances")
    state = relationship("State")
    lga = relationship("LGA")
    ward = relationship("Ward")

    # Add back_populates to AmbulanceType model later
