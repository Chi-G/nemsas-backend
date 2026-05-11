from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base

class HospitalType(Base):
    __tablename__ = "hospital_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True)
