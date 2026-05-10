from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func

class Ward(Base):
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True, default="")
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())

    lga = relationship("LGA", back_populates="wards")
