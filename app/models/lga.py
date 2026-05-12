from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class LGA(Base):
    __tablename__ = "lgas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True, default="")
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)

    state = relationship("State", back_populates="lgas")
    wards = relationship("Ward", back_populates="lga")
