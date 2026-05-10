from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    hospital_type_id = Column(Integer, ForeignKey("hospital_types.id"), nullable=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    location = Column(String, nullable=True)
    address1 = Column(String, nullable=True)
    address2 = Column(String, nullable=True)
    landmark = Column(String, nullable=True)
    nhia_or_shia = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    hospital_type = relationship("HospitalType")
    state = relationship("State")
    lga = relationship("LGA")
