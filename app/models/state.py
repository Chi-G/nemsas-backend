from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True, default="")

    lgas = relationship("LGA", back_populates="state")
